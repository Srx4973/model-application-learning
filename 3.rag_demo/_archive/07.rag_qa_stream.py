import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
import json
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

# ---------- 流式问答函数 ----------
def ask_question_stream(question):
    # 1. 检索
    results = collection.query(query_texts=[question], n_results=3)
    docs = results['documents'][0]
    metadatas = results['metadatas'][0]
    distances = results['distances'][0]

    valid = [(d, m, dist) for d, m, dist in zip(docs, metadatas, distances) if dist < 1.5]
    if not valid:
        yield "根据当前文档无法回答。"
        return

    docs, metadatas, _ = zip(*valid)  #一个*是拆包元组/列表，两个*是拆包字典
    docs, metadatas = list(docs), list(metadatas)

    context_parts = []
    source_info = []

    for i, (doc, meta) in enumerate(zip(docs, metadatas)):
        page = meta.get('page', '未知')
        context_parts.append(f"[片段{i+1}] {doc}")
        source_info.append(f"片段{i+1} 来自第 {page} 页")

    context = "\n\n".join(context_parts)
    sources = "\n".join(source_info)

    prompt = f"""请基于以下上下文回答问题。如果上下文不包含相关信息，请说“根据当前文档无法回答”。

上下文：
{context}

问题：{question}
回答："""

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
        "stream": True   #  关键：开启流式
    }

    resp = requests.post(DEEPSEEK_URL, headers=headers, json=data, stream=True)
    for line in resp.iter_lines(): #iter_lines() 会把响应的内容按行（用换行符 \n 分割）一点点输出
        #每收到一行，就执行一次循环体。
        if line:                                              #SSE（Server-Sent Events）协议规定：每条数据以 data: 开头。例如服务器发的是 data: {"choices": [...]}。
            line = line.decode("utf-8").replace("data: ", "") #把网络传输的数据是字节流解码成字符串并去掉data前缀，只保留后面的 JSON 内容
            if line == "[DONE]":  #SSE 协议里，服务器发完所有数据后，会发一条 data: [DONE] 表示“结束”。看到它，就 break 跳出循环
                break
            try:
                chunk = json.loads(line)      #把JSON 字符串解析成 Python 字典。
                delta = chunk["choices"][0]["delta"].get("content", "")
                #普通响应里是 message.content，流式里是 delta.content（delta = 增量）
                if delta:
                    yield f"data: {delta}\n\n"# 加回边界符（按照标准的 SSE 格式发出去）,告诉浏览器“强制刷新显示”的暗号
            except:
                continue

    # 3. 最后吐出参考来源
    yield f"data: \n\n 参考来源：\n" + "\n".join(source_info) + "\n\n"


# 测试：像打字机一样打印
if __name__ == "__main__":
    q = input("请输入问题：")              #end=""：打印后不换行（默认 \n），这样后续的碎片可以紧接着这句话。
    print("回答：", end="", flush=True)   #flush=True：立刻刷新缓冲区，不要等打印满一行才显示。否则“打字机效果”就没了。
    for piece in ask_question_stream(q): #调用生成器函数，每 yield 一次，就拿到一小块 piece。
        print(piece, end="", flush=True) #每拿到一块，立刻打印，不换行，立刻刷新。
    print()  # 最后换行