import os
import requests
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
# ---------- 配置区 ----------
# 线上 API 配置
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_URL = "https://api.siliconflow.cn/v1/embeddings"
RERANK_URL = "https://api.siliconflow.cn/v1/rerank"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"

# 测试集：问题 + 期望在正确文本块里看到的【唯一关键词】
TEST_DATASET = [
    {"q": "根据文档，什么是大语言模型（LLM）？", "keyword": "大型预训练语言模型"},
    {"q": "文档中提到的“缩放法则”主要揭示了什么规律？", "keyword": "扩展法则"},
    {"q": "Transformer架构的核心机制是什么？", "keyword": "自注意力"},
    {"q": "文档中介绍的混合专家模型（MoE）的主要优势是什么？", "keyword": "混合专家层"},
    {"q": "大模型预训练阶段通常使用什么类型的损失函数？", "keyword": "交叉熵"},
    {"q": "指令微调（Instruction Tuning）的主要目的是什么？", "keyword": "指令微调（Instruction Tuning）是指使用自然语言形式的数据"},
    {"q": "文档中提到的RLHF（基于人类反馈的强化学习）包含哪几个关键步骤？", "keyword": "奖励模型"},
    {"q": "文档中如何定义“智能体”（Agent）？", "keyword": "智能体规划器"},
    {"q": "在提示工程（Prompt Engineering）中，思维链（Chain-of-Thought）的核心思想是什么？", "keyword": "思维链提示"},
    {"q": "文档指出大语言模型面临的主要挑战之一“幻觉”（Hallucination）指的是什么？", "keyword": "幻象"},
]


# ---------- 线上模型类（为了兼容查询）----------
class OnlineEmbeddingFunction:
    @staticmethod
    def name() -> str: return "online_bge_m3"

    def __call__(self, input):
        if isinstance(input, str): input = [input]
        headers = {"Authorization": f"Bearer {EMBEDDING_API_KEY}"}
        data = {"model": "BAAI/bge-m3", "input": input}
        resp = requests.post(EMBEDDING_URL, headers=headers, json=data)
        return [item["embedding"] for item in resp.json()["data"]]

    def embed_query(self, input):
        return self.__call__(input)

    def embed_documents(self, input):
        return self.__call__(input)


# ---------- 重排函数 ----------
def rerank(query, docs, top_n=3):
    headers = {"Authorization": f"Bearer {EMBEDDING_API_KEY}",
               "Content-Type": "application/json"}
    data = {"model": RERANK_MODEL,
            "query": query,
            "documents": docs,
            "top_n": top_n}
    resp = requests.post(RERANK_URL, headers=headers, json=data)
    if resp.status_code == 200:
        return [item["index"] for item in resp.json()["results"]]
    return list(range(min(top_n, len(docs))))


# ---------- 核心评测逻辑 ----------
def evaluate_db(db_path, collection_name, use_rerank=False):
    print(f"\n正在评测数据库: {db_path} (重排: {'开' if use_rerank else '关'})")

    if "online" in db_path:
        embedding_fn = OnlineEmbeddingFunction()
    else:
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    client = PersistentClient(path=db_path)
    collection = client.get_collection(name=collection_name, embedding_function=embedding_fn)

    hits = 0
    total = len(TEST_DATASET)

    for item in TEST_DATASET:
        q = item["q"]
        keyword = item["keyword"]

        # 1. 检索 20 个块
        results = collection.query(query_texts=[q], n_results=20)
        docs = results['documents'][0]

        # 2. 是否重排
        if use_rerank:
            top_indices = rerank(q, docs, top_n=3)
            top_docs = [docs[i] for i in top_indices]
        else:
            top_docs = docs[:3]  # 不重排直接取前 3

        # 3. 判断是否命中
        is_hit = any(keyword in doc for doc in top_docs)
        if is_hit:
            hits += 1
            print(f"  ✅ 命中: {q}")
        else:
            print(f"  ❌ 未中: {q}")
            print(f"     [Top 1 竟然是]: {top_docs[0][:100].replace(chr(10), '')}...\n")
                                                           #把文本里的所有换行符，全部替换成空字符
    hit_rate = (hits / total) * 100
    print(f"最终命中率 (Hit@3): {hit_rate:.1f}%")#.1f 表示保留 1 位小数的浮点数
    return hit_rate


if __name__ == "__main__":
    print("=" * 50)
    print("开始 RAG 检索效果量化对比测试")
    print("=" * 50)

    # 本地库叫 chroma_db_local，线上库叫 chroma_db_online
    print("\n----- 测试 1: 本地模型 (无重排) -----")
    hit_local = evaluate_db("./chroma_db_local", "pdf_docs", use_rerank=False)

    print("\n----- 测试 2: 线上模型 (无重排) -----")
    hit_online = evaluate_db("./chroma_db_online", "pdf_docs", use_rerank=False)

    print("\n----- 测试 3: 线上模型 (开启重排) -----")
    hit_rerank = evaluate_db("./chroma_db_online", "pdf_docs", use_rerank=True)

    print("\n" + "=" * 50)
    print(" 最终对比报告：")
    print(f"本地模型 ： {hit_local}%")
    print(f"线上模型 ： {hit_online}%")
    print(f"线上+重排 ： {hit_rerank}%")
    print("=" * 50)