'''应用层 - 流式 FastAPI
启动 FastAPI 服务，提供流式输出接口，加载 index.html。
特点：这是“外壳”，通过读取不同的数据库路径，就能瞬间在“线上版”和“本地版”之间切换。
'''
import os
import json
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# ---------- 配置 ----------
from dotenv import load_dotenv
load_dotenv()


DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# 大模型（生成）的配置
MODEL_NAME = "qiniu/conatus-free"
DEEPSEEK_URL = "https://api.qnaigc.com/v1/chat/completions"


EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
# 向量模型（检索）的配置
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_URL  = "https://api.siliconflow.cn/v1/embeddings"
#重排配置
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
RERANK_URL = "https://api.siliconflow.cn/v1/rerank"


# ---------- 加载模型（线上） ----------
class OnlineEmbeddingFunction:
    @staticmethod
    def name() -> str:
        return "online_bge_m3"

    def __call__(self, input):
        # 容错处理：ChromaDB 有时传字符串，有时传列表，统一转成列表
        if isinstance(input, str):
            input = [input]

        # 调用在线 API 获取向量
        headers = {"Authorization": f"Bearer {EMBEDDING_API_KEY}"}
        data = {"model":EMBEDDING_MODEL, "input": input}
        resp = requests.post(EMBEDDING_URL, headers=headers, json=data)

        # 检查状态码（防止 Key 填错或者欠费导致解析失败）
        if resp.status_code != 200:
            print(f"Embedding API 报错: {resp.text}")
            return [[0.0] * 1024 for _ in input]  # 报错兜底，返回全0向量，防止程序直接崩掉

        # 返回向量列表
        return [item["embedding"] for item in resp.json()["data"]]
    #专门给查询用的方法
    def embed_query(self, input):
        return self.__call__(input)

    # 专门给文档入库用的方法（有些版本需要）
    def embed_documents(self, input):
        return self.__call__(input)

embedding_fn = OnlineEmbeddingFunction()

# ---------- 连接 ChromaDB ----------
client = PersistentClient(path="./chroma_db_online")
collection = client.get_or_create_collection(
    name="pdf_docs",
    embedding_function=embedding_fn,
    metadata = {"hnsw:space": "cosine"}  #使用余弦距离，余弦相似度（Cosine）
)

# ---------- FastAPI 应用 ----------
app = FastAPI(title="RAG 文档问答系统")

# 请求体模型
class AskRequest(BaseModel):
    question: str

# 响应体模型
class AskResponse(BaseModel):
    answer: str
    sources: list[str]


# ---------- 检索函数 ----------
def retrieve(query, n_results):
    results = collection.query(query_texts=[query], n_results=n_results)
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    distances = results['distances'][0]
    return docs, metas, distances

#---------- 重排函数 ----------
def rerank_documents(query, docs, top_n=3):
    """调用 API 对候选文档进行重排"""
    headers = {
        "Authorization": f"Bearer {EMBEDDING_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": RERANK_MODEL,
        "query": query,
        "documents": docs,
        "top_n": top_n
    }
    resp = requests.post(RERANK_URL, headers=headers, json=data)

    if resp.status_code != 200:
        print(f"Rerank API 报错: {resp.text}")
        # 如果重排挂了，退化为直接返回前 top_n 个原始文档的索引
        return list(range(min(top_n, len(docs))))

    # 解析返回结果，提取排好序的原始索引
    results = resp.json()["results"]
    return [item["index"] for item in results]

# -----检索、过滤、重排，拼 Prompt-----
def build_context_and_prompt(question: str):
    # 1. 粗排：去库里拿 10 个候选块
    docs, metas, distances = retrieve(question, n_results=10)

    # 2. 过滤低相似度块
    valid = [(d, m, dist) for d, m, dist in zip(docs, metas, distances) if dist < 1.5]
    if not valid:
        return None, None

    docs, metas, _ = zip(*valid)
    docs, metas = list(docs), list(metas)

    # 3. 精排：把这 10 个块丢给 Rerank API，挑出得分最高的 3 个
    print(f"粗排拿到 {len(docs)} 个候选块，正在重排...")
    top_indices = rerank_documents(question, docs, top_n=3)

    # 4. 根据重排返回的索引，提取最终的文本和元数据
    final_docs = [docs[i] for i in top_indices]
    final_metas = [metas[i] for i in top_indices]

    # 拼上下文和来源
    context_parts, source_info = [], []
    for i, (doc, meta) in enumerate(zip(final_docs, final_metas)):
        page = meta.get('page', '未知')
        context_parts.append(f"[片段{i + 1}] {doc}")
        source_info.append(f"片段{i + 1} 来自第 {page} 页")

    context = "\n\n".join(context_parts)
    sources = "\n".join(source_info)

    prompt = f"""请基于以下上下文回答问题。如果上下文不包含相关信息，请说“根据当前文档无法回答”。

上下文：
{context}

问题：{question}
回答："""
    return prompt, source_info

# ---------- 普通问答逻辑 ----------
def ask_question(question: str):
    prompt, source_info = build_context_and_prompt(question)
    if not prompt:
        return "根据当前文档无法回答。", []

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 500
    }
    resp = requests.post(DEEPSEEK_URL, headers=headers, json=data)

    if resp.status_code == 200:
        answer = resp.json()["choices"][0]["message"]["content"]
    else:
        answer = f"API 请求失败：{resp.text}"

    return answer, source_info

# -----------流式问答函数---------------
def ask_question_stream(question: str):
    # 1. 异常兜底
    try:
        prompt, source_info = build_context_and_prompt(question)
    except Exception as e:
        print(f"检索阶段异常: {e}")
        yield "data: 检索服务暂时不可用，请稍后再试。\n\n"
        return

    # 2. 空结果兜底
    if not prompt:
        yield "data: 根据当前文档无法回答。\n\n"
        return

    # 3. 调用大模型 API
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 500,
        "stream": True
    }

    try:
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=data, stream=True)
    except Exception as e:
        print(f"请求大模型异常: {e}")
        yield "data: 大模型服务网络异常，请稍后再试。\n\n"
        return

    if resp.status_code != 200:
        print(f"API请求失败，状态码：{resp.status_code}，详情：{resp.text}")
        yield "data: 系统服务出现问题，请稍后再试。\n\n"
        return

    # 4. 流式读取（新增一个变量记录完整回答）
    full_answer = ""

    for line in resp.iter_lines():
        if line:
            line_str = line.decode("utf-8")

            # 【优化点 1】用 startswith 代替 replace，防止误删正文里的 data:
            if not line_str.startswith("data: "):
                continue

            json_str = line_str[6:]  # 截取掉 "data: " 这 6 个字符
            if json_str.strip() == "[DONE]":
                break

            try:
                chunk = json.loads(json_str)
                delta = chunk["choices"][0]["delta"].get("content", "")
                if delta:
                    full_answer += delta  # 【优化点 2】累加回答，用于最后判断
                    safe = delta.replace("\n", "\ndata: ")#在每一行的开头，都插入了 data: 这个标记。
                    yield f"data: {safe}\n\n"   #这样无论模型输出多少个换行，前端按 \n\n 切分时，切出来的每一行都有合法的 data: 前缀，就不会被丢弃了。
            except json.JSONDecodeError:
                print(f"解析 JSON 失败: {json_str}")
                continue

    # 5. 【核心修改】判断大模型是否输出了“无法回答”
    # 如果包含这句话，直接 return，不输出参考来源
    if "根据当前文档无法回答" in full_answer:
        return

    # 6. 只有真正回答了，才拼接参考来源
    source_text = "\n\n参考来源：\n" + "\n".join(source_info)
    safe_sources = source_text.replace("\n", "\ndata: ")
    yield f"data: {safe_sources}\n\n"

# ---------- 接口 ----------
# 加一个路由来返回 HTML 页面
@app.get("/")
def index():
    return FileResponse("index.html")

@app.post("/ask", response_model=AskResponse)#接口最终返回的数据，必须长成 AskResponse 的样子
def ask(req: AskRequest):     #类型标注，定义了一个变量叫 req，传入的数据类型是 AskRequest
    answer, sources = ask_question(req.question)
    return AskResponse(answer=answer, sources=sources)  #实际把数据打包成标准形式（打包发货）

#流式回答接口
@app.post("/ask/stream")
def ask_stream(req: AskRequest):
    return StreamingResponse(
        ask_question_stream(req.question),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

'''流程
1.接口收到请求 → req: AskRequest 负责拆包裹、验货。
2.业务逻辑处理 → ask_question(req.question) 去查数据库、调大模型。
3.返回结果给前端 → AskResponse(answer=answer, sources=sources) 负责重新打包、贴标签，然后交给 response_model 检查后发货。
'''