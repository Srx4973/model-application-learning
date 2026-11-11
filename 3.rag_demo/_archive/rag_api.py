import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
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
DEEPSEEK_URL = "https://api.qnaigc.com/v1/chat/completions"
MODEL_NAME = "doubao-seed-2.0-mini"

# ---------- 加载本地模型（与之前一致） ----------
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# ---------- 连接 ChromaDB ----------
client = PersistentClient(path="./chroma_db1")
collection = client.get_or_create_collection(
    name="pdf_docs",
    embedding_function=embedding_fn
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


# ---------- 检索 ----------
def retrieve(query, n_results):
    results = collection.query(query_texts=[query], n_results=n_results)
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    distances = results['distances'][0]
    return docs, metas, distances


# -----检索、过滤、拼 Prompt-----
def build_context_and_prompt(question: str):
    docs, metas, distances = retrieve(question, n_results=3)

    # 过滤低相似度块
    valid = [(d, m, dist) for d, m, dist in zip(docs, metas, distances) if dist < 1.5]
    if not valid:
        return None, None

    docs, metas, _ = zip(*valid)
    docs, metas = list(docs), list(metas)

    # 拼上下文和来源
    context_parts, source_info = [], []
    for i, (doc, meta) in enumerate(zip(docs, metas)):
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
    prompt, source_info = build_context_and_prompt(question)
    if not prompt:
        yield "根据当前文档无法回答。"
        return

    # 2. 流式调用 API
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 500,
        "stream": True  # 关键：开启流式
    }

    resp = requests.post(DEEPSEEK_URL, headers=headers, json=data, stream=True)

    #流式请求先检查状态码
    if resp.status_code != 200:
        # 如果状态码不对，直接读取报错文本（此时不是流，内容很小）
        print(f"API请求失败，状态码：{resp.status_code}")
        print(f"错误详情：{resp.text}")
        yield "系统服务出现问题，请稍后再试。"
        return  # 直接结束生成器

    # 状态码正常，才进入流式读取
    for line in resp.iter_lines():  # iter_lines() 会把响应的内容按行（用换行符 \n 分割）一点点输出
        # 每收到一行，就执行一次循环体。
        if line:                                               # SSE（Server-Sent Events）协议规定：每条数据以 data: 开头。例如服务器发的是 data: {"choices": [...]}。
            line = line.decode("utf-8").replace("data: ", "")  # 把网络传输的数据是字节流解码成字符串并去掉data前缀，只保留后面的 JSON 内容
            if line == "[DONE]":  # SSE 协议里，服务器发完所有数据后，会发一条 data: [DONE] 表示“结束”。看到它，就 break 跳出循环
                break
            try:
                chunk = json.loads(line)  # 把JSON 字符串解析成 Python 字典。
                delta = chunk["choices"][0]["delta"].get("content", "")
                # 普通响应里是 message.content，流式里是 delta.content（delta = 增量）
                if delta:
                    yield f"data: {delta}\n\n"# 加回边界符（按照标准的 SSE 格式发出去）,告诉浏览器“强制刷新显示”的暗号
            except:
                continue

    # 3. 最后吐出参考来源
    yield f"data: \n\n 参考来源：\n" + "\n".join(source_info) + "\n\n"

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
    return StreamingResponse(ask_question_stream(req.question), media_type="text/event-stream")

'''流程
1.接口收到请求 → req: AskRequest 负责拆包裹、验货。
2.业务逻辑处理 → ask_question(req.question) 去查数据库、调大模型。
3.返回结果给前端 → AskResponse(answer=answer, sources=sources) 负责重新打包、贴标签，然后交给 response_model 检查后发货。
'''