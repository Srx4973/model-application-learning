***
# 个人文档智能问答系统 (RAG)

基于 **FastAPI + ChromaDB + BGE-M3** 构建的本地文档 RAG（检索增强生成）问答应用。支持读取 PDF 文档，精准检索相关片段，并通过大模型生成带有**精准页码溯源**和**流式打字机效果**的回答。

## 一.核心亮点

- **双阶段检索优化 (Recall + Rerank)**：粗排采用 `BGE-M3` 进行高精度语义召回，精排引入 `BGE-Reranker` 进行重打分，有效剔除关键词干扰。
- **量化性能对比**：内置自动化评测脚本，实测将检索策略升级为“在线 Embedding + 重排”后，**Top3 检索命中率从 30% 跃升至 80%**。
- **精准溯源与多文档支持**：采用按页切分（Chunking）策略，在 ChromaDB 中注入 `metadatas` 元数据，确保回答附带原文页码，并支持按来源过滤检索。
- **严格的 SSE 流式输出**：后端 `StreamingResponse` 配合标准 SSE 协议，前端通过 `ReadableStream` 安全解析，防吞字、防断流，实现丝滑的打字机体验。
- **工程鲁棒性保障**：包含上游 API 请求异常捕获、向量报错防崩告警、Rerank 失败自动降级，以及大模型拒答（无法回答）时的业务闭环处理（自动掐断参考来源）。

## 二.检索策略性能评测

基于自建的 10 个核心问题测试集（受限于样本量，数据用于方向性对比）：

| 检索策略 | 距离算法 | 召回数 | Top3 命中率 | 备注 |
| :--- | :--- | :--- |:---------| :--- |
| 本地 Embedding (MiniLM) | Cosine | 20 | 30%      | 中文理解弱，易被无关段落干扰 |
| 线上 Embedding (BGE-M3) | Cosine | 20 | 80%      | 中文语义理解强，大幅提升 |
| **线上 + Rerank 重排** | Cosine | 20 -> 3 | **90%**  | **双阶段检索，精准剔除噪音** |

## 三. 技术栈

- **后端框架**：FastAPI, Pydantic, Python-dotenv
- **AI 模型**：BGE-M3 (Embedding)、BGE-Reranker-v2-m3 (重排)、DeepSeek (生成)
- **向量数据库**：ChromaDB (本地持久化)
- **文档解析**：PyMuPDF (fitz)
- **前端展示**：原生 HTML + Fetch API (SSE 流式解析)

## 四.实现步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在根目录创建 `.env` 文件，填入你的 API 密钥：

```env
# 大模型 API Key (例如 DeepSeek 或 豆包)
DEEPSEEK_API_KEY="your_llm_api_key"

# SiliconFlow 向量模型与重排模型的 API Key
EMBEDDING_API_KEY="your_siliconflow_key"
```

### 3. 构建知识库

将你的 PDF 文档放入目录，修改 `build_db_online.py` 中的 `PDF_PATH` 路径，然后运行：

```bash
python build_db_online.py
```

### 4. 运行量化评测 (可选)

>  **提示**：运行此脚本前，需确保本地库 (`chroma_db_local`) 和线上库 (`chroma_db_online`) 均已建好。

```bash
python evaluate.py
```

### 5. 启动 Web 服务

>  **提示**：确保 `index.html` 位于项目根目录。

```bash
fastapi dev rag_server.py
```

启动后，浏览器访问 `http://127.0.0.1:8000/` 即可开始问答。

## 六.效果演示

**提问**
> 这份文档主要讲了什么？

**系统回答**
> 这份文档主要介绍了大语言模型相关的技术内容组织，涵盖预训练（数据准备、模型架构、训练过程）、微调与对齐（指令微调、轻量化微调、RLHF人类对齐）、大模型使用（解码与部署、提示学习）等部分，同时还涉及GPT系列模型发展历程以及相关资源信息。

---
 **参考来源**：
- 片段1 来自第 28 页
- 片段2 来自第 284 页
- 片段3 来自第 27 页