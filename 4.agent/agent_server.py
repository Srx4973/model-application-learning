import os
import json
import time
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from chromadb import PersistentClient
from fastapi.responses import StreamingResponse, FileResponse
from dotenv import load_dotenv

load_dotenv()

# ---------- 配置 ----------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL_NAME = "qiniu/conatus-free"
DEEPSEEK_URL = "https://api.qnaigc.com/v1/chat/completions"

EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_URL = "https://api.siliconflow.cn/v1/embeddings"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
RERANK_URL = "https://api.siliconflow.cn/v1/rerank"


# ---------- 向量模型 ----------
class OnlineEmbeddingFunction:
    @staticmethod
    def name() -> str:
        return "online_bge_m3"

    def __call__(self, input):
        if isinstance(input, str): input = [input]
        headers = {"Authorization": f"Bearer {EMBEDDING_API_KEY}"}
        data = {"model": EMBEDDING_MODEL, "input": input}
        resp = requests.post(EMBEDDING_URL, headers=headers, json=data)
        if resp.status_code != 200: return [[0.0] * 1024 for _ in input]
        return [item["embedding"] for item in resp.json()["data"]]

    def embed_query(self, input):
        return self.__call__(input)

    def embed_documents(self, input):
        return self.__call__(input)


embedding_fn = OnlineEmbeddingFunction()

# ---------- 数据库与检索 ----------
client = PersistentClient(path="../3.rag/chroma_db_online")
collection = client.get_or_create_collection(
    name="pdf_docs",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)


def retrieve(query, n_results):
    results = collection.query(query_texts=[query], n_results=n_results)
    return results['documents'][0], results['metadatas'][0], results['distances'][0]


def rerank_documents(query, docs, top_n=3):
    headers = {"Authorization": f"Bearer {EMBEDDING_API_KEY}", "Content-Type": "application/json"}
    data = {"model": RERANK_MODEL, "query": query, "documents": docs, "top_n": top_n}
    resp = requests.post(RERANK_URL, headers=headers, json=data)
    if resp.status_code != 200: return list(range(min(top_n, len(docs))))
    return [item["index"] for item in resp.json()["results"]]


def build_context_and_prompt(question: str):
    docs, metas, distances = retrieve(question, n_results=10)
    valid = [(d, m, dist) for d, m, dist in zip(docs, metas, distances) if dist < 1.5]
    if not valid: return None, None

    docs, metas, _ = zip(*valid)
    docs, metas = list(docs), list(metas)
    top_indices = rerank_documents(question, docs, top_n=3)

    final_docs = [docs[i] for i in top_indices]
    final_metas = [metas[i] for i in top_indices]

    context_parts, source_info = [], []
    for i, (doc, meta) in enumerate(zip(final_docs, final_metas)):
        page = meta.get('page', '未知')
        context_parts.append(f"[片段{i + 1}] {doc}")
        source_info.append(f"片段{i + 1} 来自第 {page} 页")

    context = "\n\n".join(context_parts)
    prompt = f"你是一个专业的 AI 助手。请结合以下参考资料回答用户的问题。如果参考资料里没有答案，请用你自己的知识回答，不要暴露“根据资料”这种字眼，直接像人类专家一样给出回答即可”。" \
             f"\n\n上下文：\n{context}\n\n问题：{question}\n回答："
    return prompt, source_info


# ---------- 工具定义 ----------
def get_weather(city: str) -> str:
    if "太原" in city: return "太原今天晴，气温 28 度，微风。"
    return f"{city}今天多云，气温 25 度。"


def calculate(expression: str) -> str:
    try:
        return f"计算结果是：{eval(expression)}"
    except Exception as e:
        return f"计算失败：{e}"


def search_documents(query: str) -> str:
    prompt, source_info = build_context_and_prompt(query)
    if not prompt: return "根据当前文档无法回答。"

    data = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3}
    resp = requests.post(DEEPSEEK_URL, headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}, json=data)
    if resp.status_code == 200:
        answer = resp.json()["choices"][0]["message"]["content"]
        #  核心优化：把来源信息直接打包给大模型，让它自己复述
        sources = "\n".join(source_info)
        return f"{answer}\n\n参考来源：\n{sources}"
    return "RAG 检索服务失败"


agent_tools = [
    {"type": "function", "function": {"name": "get_weather", "description": "查询指定城市的天气情况",
                                      "parameters": {"type": "object", "properties": {"city": {"type": "string"}},
                                                     "required": ["city"]}}},
    {"type": "function", "function": {"name": "calculate", "description": "计算数学表达式",
                                      "parameters": {"type": "object", "properties": {"expression": {"type": "string"}},
                                                     "required": ["expression"]}}},
    {"type": "function", "function": {"name": "search_documents", "description": "当用户询问专业知识、大模型、文档内容时，使用此工具检索本地知识库",
                                      "parameters": {"type": "object", "properties": {"query": {"type": "string"}},
                                                     "required": ["query"]}}}
]


# ---------- 通用请求函数 (带重试) ----------
def safe_request_llm(data, max_retries=3, wait_time=10):
    for attempt in range(max_retries):
        try:
            resp = requests.post(DEEPSEEK_URL, headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}, json=data,
                                 timeout=60)
            response_data = resp.json()
            if "error" in response_data:
                print(f" 触发异常：{response_data['error']['message']}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
                else:
                    return None
            return response_data
        except Exception as e:
            print(f" 网络请求异常：{e}")
            if attempt < max_retries - 1:
                time.sleep(wait_time)
            else:
                return None
    return None


# ---------- Agent 核心逻辑 ----------
def ask_agent_stream(question: str):
    messages = [{"role": "user", "content": question}]
    data = {"model": MODEL_NAME, "messages": messages, "tools": agent_tools, "temperature": 0.1}

    # 1. 判定意图
    response_data = safe_request_llm(data)
    if not response_data:
        yield "data: [SYS] 系统繁忙，请稍后再试。\n\n"
        return

    message = response_data["choices"][0]["message"]

    # 2. 如果调用工具
    if "tool_calls" in message:
        yield "data: [SYS] 正在调用工具...\n\n"
        messages.append(message)

        for tool_call in message["tool_calls"]:
            func_name = tool_call["function"]["name"]
            args = json.loads(tool_call["function"]["arguments"])
            yield f"data: [SYS] [执行 {func_name} : {args}]\n\n"

            if func_name == "get_weather":
                result = get_weather(args["city"])
            elif func_name == "calculate":
                result = calculate(args["expression"])
            elif func_name == "search_documents":
                result = search_documents(args["query"])
            else:
                result = "未知工具"

            messages.append({"role": "tool", "tool_call_id": tool_call["id"], "content": result})

        yield "data: [SYS] \n\n 正在生成最终回答...\n\n"
        data["messages"] = messages

    #最终请求不能再带 tools 字段
    data.pop("tools", None)

    # 3. 流式生成最终回答
    data["stream"] = True
    max_stream_retries = 3
    for attempt in range(max_stream_retries):
        try:
            resp = requests.post(DEEPSEEK_URL, headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}, json=data,
                                 stream=True)
            if resp.status_code != 200:
                yield "data: [SYS] 生成失败，正在重试...\n\n"
                time.sleep(20)
                continue

            for line in resp.iter_lines():
                if line:
                    line_str = line.decode("utf-8")
                    if not line_str.startswith("data: "): continue
                    json_str = line_str[6:]
                    if json_str.strip() == "[DONE]": break
                    try:
                        chunk = json.loads(json_str)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            safe = delta.replace("\n", "\ndata: ")
                            yield f"data: {safe}\n\n"
                    except:
                        continue
            break  # 成功执行完流，退出重试
        except Exception as e:
            if attempt == max_stream_retries - 1:
                yield "data: [SYS] 网络中断，生成失败。\n\n"


# ---------- FastAPI 应用 ----------
app = FastAPI(title="Agent 应用")


class AskRequest(BaseModel):
    question: str


@app.get("/")
def index():
    return FileResponse("index.html")


#  Agent 接口
@app.post("/agent/stream")
def agent_stream_api(req: AskRequest):
    return StreamingResponse(ask_agent_stream(req.question), media_type="text/event-stream")