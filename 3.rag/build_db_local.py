'''数据层 - 本地字符版
按字符切分，用本地 MiniLM 生成向量，存入 chroma_db_local 数据库。
特点：不需要联网，速度快，但语义精度较低。
'''
import os
import pymupdf
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
# ---------- 配置 ----------
PDF_PATH = "E:\\Download\\LLMBook.pdf"
CHUNK_SIZE = 512        # 每块最大字符数
CHUNK_OVERLAP = 50      # 相邻块重叠字数（防止切断语义）

# ---------- 加载模型（本地） ----------
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
# ---------- 1. 读取 PDF ----------
def load_pdf_text(path):
    # pymupdf.open() 打开 PDF
    doc = pymupdf.open(path)
    full_text = ""
    for page in doc:  # 遍历页面
        text = page.get_text("text")  # 提取纯文本
        if text:
            full_text += text + "\n"  # 存在文本则拼接并换行
    doc.close()  # 关闭文档释放内存
    return full_text

# ---------- 2. 分块 ----------
def split_text(text, chunk_size, overlap):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]  # 从第 i 个字符开始，往后取 chunk_size 个字符，
        if chunk.strip() and  len(chunk.strip()) > 50: # 保留大于 50 字符的块
            chunks.append(chunk)
    return chunks

# ---------- 主流程 ----------
if __name__ == "__main__":
    # 读取 PDF
    raw_text = load_pdf_text(PDF_PATH)
    print(f"提取文本长度：{len(raw_text)} 字符")

    # 分块
    chunks = split_text(raw_text, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"共分成 {len(chunks)} 个块")

    # 连接 ChromaDB
    client = PersistentClient(path="./chroma_db_local")
    collection = client.get_or_create_collection(
        name="pdf_docs",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # 如果集合已有数据，先清空（避免重复）
    # collection.delete_collection(“pdf_docs”)

    # 插入块（批量，每批 100 条）
    batch_size = 100    #分批处理是为了防止一次性插入几千条数据导致内存爆炸。
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        ids = [f"chunk_{j}" for j in range(i, i+len(batch))] #生成编号列表，例：（1~100），chunk_1，chunk_2...
        collection.add(
            documents=batch,
            ids=ids,
            metadatas=[{"source": "pdf_file"} for _ in batch]# _是 Python 的“匿名变量”占位符。
        )               #在这个列表推导式里，需要遍历 batch 里的每一个元素，不用关心当前元素的值是什么，只需要“循环次数”
    print(f"成功插入 {len(chunks)} 个块")

    # 测试查询
    query = "这个文档主要讲了什么？"
    results = collection.query(query_texts=[query], n_results=3)
    print("\n查询结果：")
    for doc, dist in zip(results['documents'][0], results['distances'][0]):
        print(f"- {doc[:100]}... (距离: {dist:.4f})")