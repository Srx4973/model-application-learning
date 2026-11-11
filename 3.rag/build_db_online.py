'''数据层 - 线上分页版
按页提取 PDF，用线上 BGE-M3 生成向量，存入 chroma_db_online 数据库。
特点：保留了页码溯源，向量精度高。
'''

import os
import requests
import pymupdf
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

# ---------- 配置 ----------
from dotenv import load_dotenv
load_dotenv()
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_URL  = "https://api.siliconflow.cn/v1/embeddings"
PDF_PATH = "E:\\Download\\LLMBook.pdf"
CHUNK_SIZE = 512        # 每块最大字符数
CHUNK_OVERLAP = 50      # 相邻块重叠字数（防止切断语义）

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
        data = {"model": "BAAI/bge-m3", "input": input}
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

'''主要改进：添加来源标注（显示引用页码）
要显示页码，核心是 在插入数据时就把页码存进 metadatas，
然后在查询时把这些元数据一起取出来，拼进回答里
'''

# ---------- 1. 按页读取 PDF ----------
def load_pdf_pages(path):
    doc = pymupdf.open(path)
    pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # 提取纯文本，PyMuPDF 对中文支持极好
        text = page.get_text("text")
        if text:
            pages.append((page_num + 1, text))
    doc.close()
    return pages

# ---------- 2. 分块 ----------
def split_text(text, chunk_size, overlap):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i+chunk_size] #从第 i 个字符开始，往后取 chunk_size 个字符，
        if chunk.strip():
            chunks.append(chunk)
    return chunks

# ---------- 主流程 ----------
if __name__ == "__main__":
    # 按页读取PDF
    pages = load_pdf_pages(PDF_PATH)

    all_chunks = []
    all_metadatas = []
    # 按页分块
    for page_num, text in pages:
        page_chunks = split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        for chunk in page_chunks:
            if len(chunk.strip()) < 20:  # 小于 20 字符的块丢掉
                continue

            dot_count = chunk.count('.') + chunk.count('…')
            # 如果点号 '.' 或省略号 '…' 占了整个块长度的 20% 以上，判定为目录，扔掉
            if dot_count / len(chunk) > 0.2:
                continue

            all_chunks.append(chunk)
            all_metadatas.append({"source": os.path.basename(PDF_PATH),"page": page_num})

    # 连接 ChromaDB
    client = PersistentClient(path="./chroma_db_online")
    # 先删除旧集合（如果存在），再重新创建
    try:
        client.delete_collection("pdf_docs")
        print("已删除旧集合")
    except Exception:
        print("旧集合不存在，跳过删除")

    collection = client.get_or_create_collection(
        name="pdf_docs",
        embedding_function=embedding_fn,
        metadata = {"hnsw:space": "cosine"} #使用余弦距离，余弦相似度（Cosine）
    )

    # 插入块（批量，每批 100 条）
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        collection.add(
            documents=all_chunks[i:i + batch_size],
            metadatas=all_metadatas[i:i + batch_size],
            ids = [f"chunk_{j}" for j in range(i, i+len(all_chunks[i:i + batch_size]))]
        )

    print(f" 成功插入 {len(all_chunks)} 个块，来自 {PDF_PATH}")

    # 测试查询
    query = "这个文档主要讲了什么？"
    results = collection.query(query_texts=[query], n_results=3)
    print("\n查询结果：")
    for doc, dist in zip(results['documents'][0], results['distances'][0]):
        print(f"- {doc[:200]}... (距离: {dist:.4f})")