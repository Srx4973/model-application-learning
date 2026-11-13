import requests
import json
import time
import os
from dotenv import load_dotenv
from chromadb import PersistentClient

# 配置
load_dotenv()
# 大模型的配置
API_KEY = os.getenv("DEEPSEEK_API_KEY")
URL = "https://api.qnaigc.com/v1/chat/completions"
MODEL = "qiniu/conatus-free"

# 向量模型（检索）的配置
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_URL  = "https://api.siliconflow.cn/v1/embeddings"
EMBEDDING_MODEL = "BAAI/bge-m3"

# 工具 1：天气查询（假装能查，先返回假数据）
def get_weather(city: str) -> str:
    # 真实场景下，这里会去调高德/百度的天气API
    if "太原" in city:
        return "太原今天晴，气温 28 度，微风。"
    return f"{city}今天多云，气温 25 度。"

# 工具 2：计算器
def calculate(expression: str) -> str:
    try:
        # 用 Python 自带的 eval 计算
        result = eval(expression)
        return f"计算结果是：{result}"
    except Exception as e:
        return f"计算失败：{e}"

#工具 3： rag
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
client = PersistentClient(path="../3.rag/chroma_db_online")
collection = client.get_collection(
    name="pdf_docs",
    embedding_function=embedding_fn
)

# 这是之前的 RAG 检索逻辑，
def search_documents(query: str) -> str:
    results = collection.query(query_texts=[query], n_results=3)
    docs = results['documents'][0]
    metadatas = results['metadatas'][0]
    distances = results['distances'][0]

    # 过滤：只保留距离小于 1.5 的块
    valid = [(d, m, dist) for d, m, dist in zip(docs, metadatas, distances) if dist < 1.5]
    if not valid:
        return "根据当前文档无法回答。"

    docs, metadatas, _ = zip(*valid)

    # 拼接上下文时，顺便提取页码信息
    context_parts = []
    source_info = []
    for i, (doc, meta) in enumerate(zip(docs, metadatas)):
        page = meta.get('page', '未知')
        context_parts.append(f"[片段{i + 1}] {doc}")
        source_info.append(f"片段{i + 1} 来自第 {page} 页")

    context = "\n\n".join(context_parts)
    sources = "\n".join(source_info)

# 2. 构造 Prompt
    prompt = f"""请基于以下上下文回答问题。如果上下文不包含相关信息，请说“根据当前文档无法回答”。

上下文：
{context}

问题：{query}
回答："""

    # 3. 调用 API
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,  # 降低随机性，更严谨
        "max_tokens": 500
    }
    resp = requests.post(URL, headers=headers, json=data)
    if resp.status_code == 200:
        answer = resp.json()["choices"][0]["message"]["content"]
        # 在回答末尾强制附加引用来源
        return f"{answer}\n\n 参考来源：\n{sources}"
    else:
        return f"API 请求失败：{resp.text}"


#给大模型的说明书
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，例如：太原、北京",
                    }
                },
                "required": ["city"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式，例如：123 * 456",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式",
                    }
                },
                "required": ["expression"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "当用户询问关于大模型、论文、技术文档、课程内容等专业知识时，使用此工具检索本地知识库",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "用户的问题或检索关键词",
                    }
                },
                "required": ["query"],
            },
        }
    }
]

#封装带重试的请求函数
def safe_request_llm(data, max_retries=3, wait_time=20):
    """带自动重试机制的大模型请求函数"""
    for attempt in range(max_retries):
        try:
            resp = requests.post(URL, headers={"Authorization": f"Bearer {API_KEY}"}, json=data, timeout=60)
            response_data = resp.json()

            # 如果返回了 error 字段（例如限流、余额不足等）
            if "error" in response_data:
                error_msg = response_data['error']['message']
                print(f" 触发异常：{error_msg}")
                if attempt < max_retries - 1:
                    print(f"等待 {wait_time} 秒后进行第 {attempt + 1} 次重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print("已达到最大重试次数。")
                    return None

            # 没有 error，直接返回结果
            return response_data
        #如果网络问题
        except Exception as e:
            print(f" 网络请求异常：{e}")
            if attempt < max_retries - 1:
                print(f" 等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                return None
    return None

#大模型决策
def ask_agent(user_question):
    messages = [{"role": "user", "content": user_question}]

    # 1. 第一次请求：带上 tools 列表
    data = {
        "model": MODEL,
        "messages": messages,
        "tools": tools,  # 把说明书交给大模型
        "temperature": 0.1
    }

    response_data = safe_request_llm(data)
    if not response_data:
        return "系统繁忙，请稍后再试。（第一次请求失败）"

    message = response_data["choices"][0]["message"]

    # 2. 判断大模型是不是要调工具
    if "tool_calls" in message:
        print("\n大模型决定调用工具！")
        messages.append(message)  # 把大模型的决策（包含 tool_calls）加进历史记录

        # 3. 你的程序负责干活
        for tool_call in message["tool_calls"]:
            func_name = tool_call["function"]["name"]
            # 获取大模型想要传的参数
            args = json.loads(tool_call["function"]["arguments"])
            print(f"准备执行：{func_name}，参数：{args}")

            # 执行本地函数
            if func_name == "get_weather":
                result = get_weather(args["city"])
            elif func_name == "calculate":
                result = calculate(args["expression"])
            elif func_name == "search_documents":  # rag文档
                result = search_documents(args["query"])
            else:
                result = "未知工具"

            # 4. 把执行结果包装成 "tool" 消息，塞回历史记录
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": result
            })

        # 5. 第二次请求：把执行结果喂给大模型，让它做最终总结
        data["messages"] = messages
        # 第二次请求不需要再传 tools 了
        data.pop("tools", None)

        final_response_data = safe_request_llm(data)
        if not final_response_data:
            return "工具执行完毕，但总结生成失败（第二次请求被限流，请稍后再试）。"

        final_answer = final_response_data["choices"][0]["message"]["content"]
        return final_answer

    else:
        # 如果没调工具，直接返回大模型的回答
        return message["content"]


if __name__ == "__main__":
    questions = [
        "太原今天天气怎么样？",  # 应该触发天气
        "123 * 456 等于多少？",  # 应该触发计算器
        "大语言模型是什么？",  # 应该触发 RAG 检索
        "帮我查查太原的天气，另外大语言模型的定义是什么？"  # 应该同时触发两个工具！
    ]

    for q in questions:
        print("\n" + "=" * 40)
        print(f"用户：{q}")
        answer = ask_agent(q)
        print(f"AI: {answer}")
