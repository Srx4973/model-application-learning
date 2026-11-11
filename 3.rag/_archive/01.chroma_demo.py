'''
__init__：是 “构造函数”，在 创建对象时 执行（obj = MyClass()）。

__call__：是 “调用函数”，在 把对象当函数使用时 执行（obj(input_text)）。
'''

import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import chromadb
from chromadb.utils import embedding_functions

# 直接使用内置函数
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="my_docs",
    embedding_function=embedding_fn
)

collection.add(
    documents=["我喜欢吃苹果", "I like apples", "苹果是一种水果"],
    metadatas=[{"source": "sentence1"}, {"source": "sentence2"}, {"source": "sentence3"}],
    #metadatas 是用来存“标签”和“背景信息”的，它让向量检索从“盲目”变成“精准”。
    ids=["id1", "id2", "id3"]
)

results = collection.query(
    query_texts=["苹果好吃吗？"],
    n_results=3            #返回 Top-K 个最相似的结果
)
print(results)