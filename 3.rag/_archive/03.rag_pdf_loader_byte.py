import os
from pypdf import PdfReader
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
    reader = PdfReader(path)
    full_text = ""
    for page in reader.pages:        #遍历页面
        text = page.extract_text()   #从页面提取文本
        if text:
            full_text += text + "\n" #如果文本存在，加上并换行
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
    client = PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(
        name="pdf_docs",
        embedding_function=embedding_fn
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

'''results 是一个字典，包含四个字段（每个字段都是一个二维列表）：
1.'ids'：返回记录的 ID（如 ["chunk_0", "chunk_5", "chunk_3"]）
2.'documents'：返回记录的原文文本（3 个字符串）
3.'metadatas'：返回记录的标签（3 个字典）
4.'distances'：返回相似度距离（数值越小越相关）

a.results['documents'][0]：是一个列表，里面装着检索到的文本（比如 3 条）。
b.results['distances'][0]：是一个列表，里面装着对应的相似度距离（越小越相关）。
c.zip()：像拉链一样，把两个列表一对一“拉”在一起。第一条文本配第一个距离，第二条配第二个...
d.for doc, dist in zip(...)：同时拿到“文本”和“距离”，分别赋值给 doc 和 dist 变量。
'''

'''ChromaDB 支持批量查询（Batch Query）。
你可以一次性把 10 个不同的问题丢进去，它会一次性返回 10 组结果。这比写 10 次 for 循环快得多。
如果你只查 1 个问题，外层维度就是 1，但 ChromaDB 依然按“列表套列表”的格式返回，方便你用 [0] 取唯一的那一组。

外层维度 = 你的问题数（此处为 1），内层维度 = 你设定的返回条数（此处为 3）
'''