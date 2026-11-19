import os
import time
import pymupdf
import requests
from celery import Celery
from chromadb import PersistentClient
from dotenv import load_dotenv

load_dotenv()

# ================= 1. Celery 配置 =================
# 初始化 Celery
# broker 负责接收任务指令（Redis 的 0 号库）
# backend 负责存放任务结果和进度（Redis 的 1 号库）
celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

# ================= 2. 配置 API =================
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_URL = "https://api.siliconflow.cn/v1/embeddings"


class OnlineEmbeddingFunction:
    @staticmethod
    def name() -> str:
        return "online_bge_m3"

    def __call__(self, input):
        if isinstance(input, str): input = [input]
        headers = {"Authorization": f"Bearer {EMBEDDING_API_KEY}"}
        data = {"model": "BAAI/bge-m3", "input": input}
        resp = requests.post(EMBEDDING_URL, headers=headers, json=data)
        if resp.status_code != 200:
            print(f"Embedding API 报错: {resp.text}")
            return [[0.0] * 1024 for _ in input]
        return [item["embedding"] for item in resp.json()["data"]]

    def embed_query(self, input):
        return self.__call__(input)

    def embed_documents(self, input):
        return self.__call__(input)


embedding_fn = OnlineEmbeddingFunction()


# ================= 3. 工具函数 =================
#按页读取
def load_pdf_pages(path):
    doc = pymupdf.open(path)
    pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        if text: pages.append((page_num + 1, text))
    doc.close()
    return pages

#分块
def split_text(text, chunk_size, overlap):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if chunk.strip(): chunks.append(chunk)
    return chunks


# ================= 4. 核心 Celery 任务 =================
@celery_app.task(bind=True) #@celery_app.task：告诉 Celery 这是一个后台任务。bind=True：意思是把任务实例本身（self）传进函数里
def process_pdf_to_db(self, pdf_path, chunk_size=512, chunk_overlap=50):
    """把 PDF 解析并存入 ChromaDB 的后台任务"""

    # 更新初始状态
    self.update_state(state="PROGRESS", meta={"progress": 5, "message": "正在读取 PDF 页面..."})

    # 1. 读取 PDF
    try:
        pages = load_pdf_pages(pdf_path)
    except Exception as e:
        return {"status": "error", "message": f"PDF读取失败: {e}"}

    all_chunks = []
    all_metadatas = []

    self.update_state(state="PROGRESS", meta={"progress": 15, "message": "正在分块与清洗数据..."})

    # 2. 分块与清洗
    for page_num, text in pages:
        page_chunks = split_text(text, chunk_size, chunk_overlap)
        for chunk in page_chunks:
            if len(chunk.strip()) < 20: continue
            dot_count = chunk.count('.') + chunk.count('…')
            if dot_count / len(chunk) > 0.2: continue

            all_chunks.append(chunk)
            all_metadatas.append({"source": os.path.basename(pdf_path), "page": page_num})

    if not all_chunks:
        return {"status": "error", "message": "未提取到有效文本块"}

    # 3. 连接数据库
    self.update_state(state="PROGRESS", meta={"progress": 20, "message": "连接数据库..."})
    client = PersistentClient(path="../3.rag/chroma_db_online")
    try:
        client.delete_collection("pdf_docs")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name="pdf_docs",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # 4. 分批次插入（最耗时的部分，也是进度条的核心）
    batch_size = 100
    total_steps = (len(all_chunks) + batch_size - 1) // batch_size  # 向上取整计算总批次数

    for step, i in enumerate(range(0, len(all_chunks), batch_size), start=1):
        # 提取当前批的数据
        batch_docs = all_chunks[i:i + batch_size]
        batch_metas = all_metadatas[i:i + batch_size]
        batch_ids = [f"chunk_{j}" for j in range(i, i + len(batch_docs))]

        # 插入数据库
        collection.add(documents=batch_docs, metadatas=batch_metas, ids=batch_ids)

        # 计算百分比进度 (20% 起，90% 止，留 10% 给最后收尾)
        progress = int(20 + (step / total_steps) * 70)

        self.update_state(
            state="PROGRESS",
            meta={
                "progress": progress,
                "message": f"正在向量化并入库: 已处理 {step}/{total_steps} 个批次..."
            }
        )

    # 5. 任务完成
    return {
        "status": "success",
        "message": f"成功插入 {len(all_chunks)} 个文本块",
        "file": os.path.basename(pdf_path)
    }