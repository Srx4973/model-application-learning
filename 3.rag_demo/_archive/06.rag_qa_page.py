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
client = PersistentClient(path="./chroma_db1")
collection = client.get_or_create_collection(
    name="pdf_docs",
    embedding_function=embedding_fn
)


# ---------- 检索函数（复用） ----------
def retrieve(query, n_results=3):
    results = collection.query(query_texts=[query], n_results=n_results)
    # 返回文本列表和 元数据列表（包含页码）
    return results['documents'][0], results['metadatas'][0],results['distances'][0]


# ---------- 调用 DeepSeek Chat 生成回答 ----------
def ask_question(question):
    '''新增改进:过滤低相似度块'''

    # 1. 检索相关块
    docs, metadatas, distances = retrieve(question, n_results=3)

    # 过滤：只保留距离小于 1.5 的块
    valid = [(d, m, dist) for d, m, dist in zip(docs, metadatas, distances) if dist < 1.5]
    if not valid:
        return "根据当前文档无法回答。"

    docs, metadatas, _ = zip(*valid) #一个*是拆包元组/列表，两个*是拆字典

    # 新逻辑：拼接上下文时，顺便提取页码信息
    context_parts = []
    source_info = []
    for i, (doc, meta) in enumerate(zip(docs, metadatas)):
        page = meta.get('page', '未知')
        context_parts.append(f"[片段{i + 1}] {doc}")
        source_info.append(f"片段{i + 1} 来自第 {page} 页")

    '''
    context_parts 里装的是文本块（比如 [片段1] 这是一段很长的文字...、[片段2] 另一段文字...）。

    用途：这段拼接结果会被塞进 Prompt，让大模型去阅读。
    为什么用 \n\n：双换行在 Markdown 和大多数文本格式里代表“段落分隔”。
    用双换行，大模型能清楚地识别出：“片段1 结束了，片段2 是新的独立段落。”
    如果用单换行，多个片段会挤在一起，大模型可能会把它们当成同一段连续的话，导致理解偏差或混淆引用。
    '''
    context = "\n\n".join(context_parts)
    sources = "\n".join(source_info)
    '''
    sources = "\n".join(source_info) —— 为什么用一个换行？

    source_info 里装的是来源信息（比如 片段1 来自第 3 页、片段2 来自第 5 页）。
    用途：这段拼接结果会作为附注展示在回答末尾，给人看。
    为什么用 \n：单换行在显示时就是“换行”，每条来源占一行，看起来清清爽爽。
    如果用双换行，每条来源之间会多出一个空行，看起来松散、浪费屏幕空间。
    而且来源信息本身是短句，不需要“段落分隔”的语义。
    '''

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
        # 在回答末尾强制附加引用来源
        return f"{answer}\n\n 参考来源：\n{sources}"
    else:
        return f"API 请求失败：{resp.text}"


# ---------- 测试 ----------
if __name__ == "__main__":
    q = "这份文档主要讲了什么？"
    ans = ask_question(q)
    print(f"问题：{q}\n回答：{ans}")