import os
# 设置镜像源（放在导入之前）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from sentence_transformers import SentenceTransformer

# 使用更小的模型（80MB），下载更快
model = SentenceTransformer('all-MiniLM-L6-v2')

vec1 = model.encode("我喜欢吃苹果")
vec2 = model.encode("I like apples")

print(f"向量长度: {len(vec1)}")   # 384
print(f"前5个值: {vec1[:5]}")


'''
二.计算余弦相似度
'''
import math

def cosine_similarity(v1, v2):
    # 点积
    dot = sum(a * b for a, b in zip(v1, v2))
    # 模长
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0

# 测试
sim = cosine_similarity(vec1, vec2)
print(f"“我喜欢吃苹果” 和 “I like apples” 的相似度：{sim:.4f}")
# 期望输出接近 0.8~0.9（因为语义相近）
