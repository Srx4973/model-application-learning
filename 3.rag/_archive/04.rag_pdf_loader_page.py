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


'''主要改进：添加来源标注（显示引用页码）
要显示页码，核心是 在插入数据时就把页码存进 metadatas，
然后在查询时把这些元数据一起取出来，拼进回答里
'''

# ---------- 1. 按页读取 PDF ----------
def load_pdf_pages(path):
    # 返回一个列表，每个元素是 (页码, 该页文本)
    reader = PdfReader(path)
    pages = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text:
            pages.append((page_num, text))
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
            if len(chunk.strip()) < 50:  # 小于 50 字符的块丢掉
                continue
            all_chunks.append(chunk)
            all_metadatas.append({"source": os.path.basename(PDF_PATH),"page": page_num})

    # 连接 ChromaDB
    client = PersistentClient(path="./chroma_db1")

    # 先删除旧集合（如果存在），再重新创建
    try:
        client.delete_collection("pdf_docs")
        print("已删除旧集合")
    except Exception:
        print("旧集合不存在，跳过删除")

    collection = client.get_or_create_collection(
        name="pdf_docs",
        embedding_function=embedding_fn
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
    query = "这个论文主要讲了什么？"
    results = collection.query(query_texts=[query], n_results=3)
    print("\n查询结果：")
    for doc, dist in zip(results['documents'][0], results['distances'][0]):
        print(f"- {doc[:200]}... (距离: {dist:.4f})")

