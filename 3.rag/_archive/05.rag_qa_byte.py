import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
import requests
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

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
client = PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="pdf_docs",
    embedding_function=embedding_fn
)

# ---------- 检索函数（复用） ----------
def retrieve(query, n_results=3):
    results = collection.query(query_texts=[query], n_results=n_results)
    return results['documents'][0]  # 返回文本列表

# ---------- 调用 DeepSeek Chat 生成回答 ----------
def ask_question(question):
    # 1. 检索相关块
    docs = retrieve(question, n_results=3)
    context = "\n\n".join(docs)  # 用换行拼接

    # 2. 构造 Prompt
    prompt = f"""请基于以下上下文回答问题。如果上下文不包含相关信息，请说“根据当前文档无法回答”。

上下文：
{context}

问题：{question}
回答："""

    # 3. 调用 API
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,  # 降低随机性，更严谨
        "max_tokens": 500
    }
    resp = requests.post(DEEPSEEK_URL, headers=headers, json=data)
    if resp.status_code == 200:
        answer = resp.json()["choices"][0]["message"]["content"]
        return answer
    else:
        return f"API 请求失败：{resp.text}"

# ---------- 测试 ----------
if __name__ == "__main__":
    q = "这份文档主要讲了什么？"
    ans = ask_question(q)
    print(f"问题：{q}\n回答：{ans}")