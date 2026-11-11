# RAG 项目学习笔记

> 用途：主笔记 / 复习清单 / 面试速记  
> 组织方式：选型 → 技术点 → 踩坑 → 评测 → Checklist → 速记

---

## 项目文件地图

| 文件 | 作用 | 关键点 |
|---|---|---|
| `01.chroma_demo.py` | ChromaDB 入门 | `PersistentClient`、`add/query`、metadata、`__call__` |
| `02.embedding_demo.py` | Embedding 与余弦相似度 | 文本转向量、384 维、余弦公式 |
| `03.rag_pdf_loader_byte.py` | PDF 全文读取 + 本地向量库 | 全文拼接、按字符分块、本地 MiniLM |
| `04.rag_pdf_loader_page.py` | PDF 按页读取 + 页码元数据 | `page` 写入 metadata，支持溯源 |
| `05.rag_qa_byte.py` | 基础 RAG 问答 | 检索 Top3 + Prompt + 调大模型 |
| `06.rag_qa_page.py` | 带页码引用的 RAG 问答 | 过滤低相似度、拼接来源页码 |
| `07.rag_qa_stream.py` | 命令行流式问答 | 生成器 `yield`、SSE 解析 |
| `build_db_local.py` | 本地向量库构建 | 全文分块、MiniLM、`chroma_db_local` |
| `build_db_online.py` | 线上向量库构建 | 按页分块、BGE-M3、`chroma_db_online` |
| `evaluate.py` | 检索效果评测 | 10 题 Hit@3、三组对比 |
| `rag_api.py` | 本地版 FastAPI 服务 | 本地库 + 普通/流式接口 |
| `rag_server.py` | 线上版 FastAPI 服务 | 线上库 + Rerank + 流式 |
| `index.html` | 前端页面 | fetch 读流、TextDecoder、打字机 |

---

## 1. 核心架构选型

### 1.1 分块：按页 > 按字符

| 方案 | 做法 | 优点 | 缺点 |
|---|---|---|---|
| 按字符 | 整本书拼成一串，每 512 字符硬切 | 简单 | 块可能跨页，页码不准 |
| 按页 | 每页单独切，metadata 写页码 | 页码精准，可溯源 | 页内仍 512 硬切，页末/下页开头语义会断 |

**选择：按页分块。**  
页码可溯源，用户能回原文验证。彻底解决语义断裂需按段落/标题切，或滑动窗口 + 页码映射。

### 1.2 输出：流式 > 普通

- 普通请求：白屏等 15 秒，体验差。
- SSE 流式：打字机效果，AI 产品标配。
- 已知风险：来源在流尾追加，若正文末尾无空行会紧贴正文；前端补 `\n\n` 可解决。

**选择：流式输出。**

### 1.3 入库：带 metadata（来源信息） > 不带

```python
{"source": 文件名, "page": 页码}
```

作用：
- 缓解幻觉，回答可溯源。
- 支持 `where={"source": ...}` 按来源过滤检索，多文档刚需。

**没有出处的 RAG 就是耍流氓。**

---

## 2. 一句话总流程

> PDF 按页读取 → 分块写页码 metadata → Embedding 入 ChromaDB（cosine）→ 提问检索 Top-K → 过滤低相似度 → Rerank 精排 → 拼 Prompt → 大模型流式生成 → SSE 逐块推前端 → 打字机显示 + 文末附来源。

---

## 3. 关键技术点速查

### 3.1 Embedding

- Embedding 把文本映射成向量，语义相近 → 向量相近。
- 维度：MiniLM = 384，BGE-M3 = 1024。
- **铁律：入库和查询必须用同一个 Embedding 模型/函数。** 否则向量空间不一致，检索无效。
- 自定义类：`__init__` 创建时执行，`__call__` 对象当函数调用时执行（ChromaDB 依赖 `__call__`）。
- 线上 API 容错：状态码非 200 返回全 0 向量可防崩，但会静默降质。生产应重试 + 抛异常 + 告警。

### 3.2 ChromaDB

```python
client = PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="pdf_docs",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)
```

要点：
- `PersistentClient(path=...)` 持久化到本地目录。
- 默认 L2 距离；BGE-M3 / MiniLM 都建议显式设 `cosine`。
- `add(documents, metadatas, ids)`，每批约 100 条，防内存爆炸。
- `query(query_texts=[q], n_results=k)` 返回二维列表：
  - 外层 = 问题数
  - 内层 = Top-K
  - 取第一个问题：`results["documents"][0]`
  
### 3.3 PDF 读取与分块

- `pypdf` 中文易乱码 → 换 `PyMuPDF (fitz)`，`page.get_text("text")`，速度快、中文好。
- 全文版：所有页拼成 `full_text`，分块简单但无页码。
- 按页版：每页单独分块，metadata 存 `page`，支持引用溯源。
- 分块参数：
  - `CHUNK_SIZE = 512`
  - `CHUNK_OVERLAP = 50`，防切断语义
- 过滤：
  - 短块过滤：小于 20/50 字符丢掉。
  - 目录过滤：点号/省略号占比 > 20% 判为目录，丢掉。
   ```python
   dot_count = chunk.count('.') + chunk.count('…')
   if dot_count / len(chunk) > 0.2:
           continue
   ```

### 3.4 检索、过滤与重排

**3.4.1 基础检索**
```python
results = collection.query(query_texts=[query], n_results=20)
docs = results["documents"][0]
metas = results["metadatas"][0]
distances = results["distances"][0]
```

**3.4.2 低相似度过滤**
```python
valid = [(d, m, dist) for d, m, dist in zip(docs, metas, distances) if dist < 1.5]
```
- `1.5` 是经验阈值，换模型/库需重调。
- 若全被过滤 → 回答“根据当前文档无法回答”。

**3.4.3 拆包**
```python
docs, metas, _ = zip(*valid)
```
- `*valid` 把列表拆成参数。`zip(*valid)` 把 `(doc, meta, dist)` 重新拆成三列。
- `*` 拆元组/列表，`**` 拆字典。

**3.4.4 Rerank 双阶段**
1. 向量粗排召回 10/20 个候选。
2. BGE-Reranker 精排取 Top3。
- 注意：Rerank 返回的是**原始候选索引**，要用 `docs[i]` 回取。失败退化取前 `top_n`，服务不挂。
```python
final_docs = [docs[i] for i in top_indices]
```

### 3.5 Prompt 拼接与来源

```python
context = "\n\n".join(context_parts)
sources = "\n".join(source_info)
```

- `context` 用 `\n\n`：分段，让模型识别独立片段。
- `sources` 用 `\n`：每条来源一行，给人看。
- `meta.get("page", "未知")` 安全取页码。
- 生成参数：`temperature=0.3` 降随机，`max_tokens=500` 控长。

Prompt 模板核心：
> 请基于以下上下文回答问题。如果上下文不包含相关信息，请说“根据当前文档无法回答”。

### 3.6 FastAPI 外壳

```python
class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    sources: list[str]
```

- Pydantic：拆包验货 → 打包发货。
- `response_model=AskResponse` 强约束返回结构。
- `FileResponse("index.html")` 返回页面。
- `StreamingResponse(gen(), media_type="text/event-stream")` 流式响应。

### 3.7 SSE 前后端契约（重点）

后端每条 `yield` 都必须是：`data: xxx\n\n`。关键：**delta 内换行要转成 `\ndata: `**。

```python
safe = delta.replace("\n", "\ndata: ")
yield f"data: {safe}\n\n"
```
**为什么必转**：模型一个 chunk 常带 `"第一段\n\n第二段"`， 我们强行在每一行的开头，都插入了 data: 这个标记。
这样无论模型输出多少个换行，前端按 \n\n 切分时，切出来的每一行都有合法的 data: 前缀，就不会被丢弃了。

**a. 前端标准解析**
1. 按 `\n\n` 切事件。
2. 只认 `data: ` 前缀。
3. `substring(6)` 去掉前缀。
4. `replace(/\ndata: /g, "\n")` 还原换行。

**b. 上游 SSE 解析**
- 用 `line.startswith("data: ")`，不要用 `replace("data: ", "")`，避免误删正文里的 `data: `。
- 遇 `[DONE]` 结束循环。
- `iter_lines()` 按行读，`decode("utf-8")` 字节转字符串。
- 普通响应取 `message.content`，流式取 `delta.content`。
- 反代场景加 `X-Accel-Buffering: no`。

**c. 来源在流尾追加**
```python
source_text = "\n\n参考来源：\n" + ...
source_text = source_text.replace("\n", "\ndata: ")
yield f"data: {source_text}\n\n"
```
保证每行带 `data: ` 前缀，多行来源可完整显示。

---

## 4. 踩坑与已知风险

| 坑/风险 | 现象 | 解决/反思 |
|---|---|---|
| pypdf 中文乱码 | 技术书大量乱码 | 换 PyMuPDF `fitz`，`page.get_text("text")` |
| ChromaDB 默认 L2 | 相关段落距离高、排序乱 | 建库显式设 `metadata={"hnsw:space": "cosine"}`，本地/线上都要设 |
| 异常兜底失效 | `requests.post` 超时抛异常，走不到 `if not prompt` | `try/except` 接异常，`if not prompt` 接空结果，两道关串联 |
| 全 0 向量兜底 | API 报错返回 `[[0.0]*1024...]`，静默降质 | 生产改重试 + 抛异常 + 告警 |
| **上游解析吞字** | 用 `replace("data: ", "")` 解析，误删正文里的 `data: ` | **改用 `startswith("data: ")` 判断，切片 `[6:]` 去除前缀** |
| **无法回答却带来源** | 大模型说“无法回答”，但流结束后仍拼接了 `source_info` | **流式累加 `full_answer`，若判定无法回答则直接 `return` 掐断来源** |
| 来源紧贴正文 | 流尾来源无空行 | 前端补 `\n\n`，来源每行带 `data: ` 前缀 |
| 前端粗暴 replace | 正文含 `data:`/空行会被误删 | 标准 SSE 事件切分解析 |
| 同步 requests 阻塞 | 流式生成器里阻塞 worker | 多用户换 `httpx.AsyncClient` + `async def` |
| 前端 buffer 残留 | 流被截断 | 处理 buffer 残留逻辑 |
| 距离阈值 1.5 | 换模型失效 | 经验值，需重调 |
| 目录/短块过滤 | 可能误杀正常内容 | 观察效果，调阈值 |

---

## 5. 量化评测

10 题评估集，统一 20 召回、统一 cosine，保证对比公平。

| 策略 | 距离 | 召回 | Hit@3 | 说明 |
|---|---|---|------:|---|
| 本地 MiniLM | cosine | 20 | 30% | 中文弱，噪音多 |
| 线上 BGE-M3 | cosine | 20 | 80% | 语义强，大幅提升 |
| 线上 + Rerank | cosine | 20 → 3 | 90% | 双阶段，精准剔除噪音 |

备注：
- 样本仅 10 题，Hit@3 置信区间宽，只做方向性对比，非绝对精度。
- 评测与服务召回数一致（均 20），结论可迁移。
- Rerank 多一次 API 调用，有几十毫秒延迟成本。
- 本地库漏设 cosine 会污染评测；本表已修。

### 架构视野：从 Demo 评测到企业级评测

目前项目采用的是基于自建测试集的轻量级评测（Hit@3），用于快速验证方案（如向量模型、重排序）的优劣。如果将该系统推向企业级生产环境，评测体系需要升级为“三级评测架构”：

#### 1. 检索阶段评测 (基于 MTEB 框架)
- **核心指标**：除了现有的 HitRate（是否命中），还需引入 MRR（平均倒数排名，衡量第一个正确结果排多前）和 NDCG（按位置折损的累积增益）。
- **数据要求**：需要人工标注 Corpus（语料）、Queries（问题）以及 Query Relevances（相关性得分）。

#### 2. 生成阶段评测 (基于 RAGAS 框架)
- **核心指标**：
  - **忠实度 (Faithfulness)**：将生成的答案拆句，让大模型判断是否能由检索到的上下文推出（防幻觉）。
  - **正确率 (Answer Correctness)**：将标准答案与实际答案拆句算 F1 值。
  - **相关性**：根据生成的答案反推问题，看与原问题的相似度。

#### 3. 评测方法架构
- **“自动指标兜底 + 大模型规模化评测 + 人工抽样校准”**：
  - 传统自动指标便宜、死板；
  - 大模型评测（LLM as a Judge）兼顾成本与可信度；
  - 人工评测成本高，但用于校准大模型评测的准确性。
---


## 6. 易错 Checklist

### 建库/检索
- [ ] 入库与查询 Embedding 模型一致。
- [ ] 本地库、线上库都设 `cosine`。
- [ ] 目录过滤：`./…` 占比 > 20% 丢掉。
- [ ] 短块过滤阈值合适。
- [ ] metadata 必含 `page`。
- [ ] 重建集合用 `client.delete_collection("pdf_docs")`。
- [ ] 不同库的 embedding 函数不能混用查询。
- [ ] `OnlineEmbeddingFunction.name()` 是 ChromaDB 识别所需。

### Rerank
- [ ] 返回的是索引，用 `docs[i]` 回取。
- [ ] 失败有退化逻辑，取前 `top_n`。

### 流式 SSE
**1. 后端发送（生产者）**
- [ ] 所有 `yield` 必须是 `data: xxx\n\n`；正文和来源内部的 `\n` 必须转义为 `\ndata: `。
- 
**2. 上游接收（消费者）**
- [ ] 先查 `status_code` 再 `iter_lines()`。
- [ ] 用 `startswith("data: ")` 判断并用切片截取，绝不全局 `replace`。
- 
**3. 前端接收（展示端）**
- [ ] 前端严格按 `\n\n` 切事件解析，不用全局 `replace`。
- [ ] 反代场景下 `StreamingResponse` 加 `X-Accel-Buffering: no`。
- 
**4. 业务边界（闭环节点）**
- [ ] 累加 `full_answer`，若大模型判定“无法回答”直接 `return`，不附带来源。

### 异常兜底
- [ ] `try/except` 包检索调用。
- [ ] `if not prompt` 接空结果。
- [ ] 两者串联，不混在同一个 `try` 里。

```python
# 异常兜底正确写法
try:
    prompt, source_info = build_context_and_prompt(question)
except Exception:
    yield "data: 检索服务暂时不可用，请稍后再试。\n\n"
    return

if not prompt:
    yield "data: 根据当前文档无法回答。\n\n"
    return
```

### 生产化
- [ ] **全 0 向量兜底风险**：API 报错时返回全 0，会导致余弦相似度 0/0 或排末尾。需改为重试 + 抛异常 + 告警（避免静默降质）。
- [ ] **同步阻塞 worker 风险**：同步生成器里的 `requests.post` 会阻塞事件循环。多用户场景需换 `httpx.AsyncClient` + `async def` 改为异步。
---

## 7. 面试八股速记

1. **Embedding 原则**：入库和查询必须同模型。
2. **ChromaDB 返回**：永远二维列表，`[0]` 取第一问题。
3. **Python 拆包**：`*valid` 拆列表，`zip(*valid)` 重列；`*` 拆元组/列表，`**` 拆字典。
4. **SSE 三要素**：`data: ` 前缀、`\n\n` 事件边界、`[DONE]` 结束。
5. **流式生成器**：`yield` 产块，`for piece in ...` 消费，`flush=True` 才有打字机。
6. **Rerank 双阶段**：向量粗排召回 → Reranker 精排 → 取 Top3。
7. **兜底两层**：`try/except` 接异常，`if not prompt` 接空结果。
8. **页码溯源**：分块写 metadata，查询取 `metadatas` 拼进 Prompt 和来源。
9. **分块选型**：按页 > 按字符，页码可溯源；彻底解决语义断裂需段落/标题切或滑动窗口。
10. **流式风险**：delta 内换行必须转 `\ndata: `，否则前端按 `\n\n` 切事件会丢内容。
```