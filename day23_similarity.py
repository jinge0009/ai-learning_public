import os
import math
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model="kinfra-text-embedding-0.6b",
        input=text,
        encoding_format="float"
    )
    return response.data[0].embedding

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """余弦相似度，越接近 1 越相似"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)

if __name__ == "__main__":
    texts = [
        "我喜欢猫",
        "我爱猫咪",
        "今天下雨了",
        "Python是一门编程语言"
    ]

    print("生成向量中...")
    embeddings = [get_embedding(t) for t in texts]

    print("\n相似度矩阵：")
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            print(f"{texts[i]} vs {texts[j]}: {sim:.4f}")