import os
import math
from dotenv import load_dotenv
from openai import OpenAI
from day22_load import load_document
from day23_split import split_text

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

def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)

if __name__ == "__main__":
    # 1. 加载 + 切分
    text = load_document("sample.pdf")
    chunks = split_text(text, chunk_size=100, chunk_overlap=20)
    print(f"文档切分成 {len(chunks)} 块\n")

    # 2. 每块生成向量
    print("生成向量中...")
    chunk_embeddings = [get_embedding(c) for c in chunks]
    print(f"完成 {len(chunk_embeddings)} 个向量\n")

    # 3. 检索
    query = "什么是 FastAPI？"
    print(f"查询：{query}\n")

    query_vec = get_embedding(query)
    scores = [
        (cosine_similarity(query_vec, emb), chunk)
        for emb, chunk in zip(chunk_embeddings, chunks)
    ]
    scores.sort(reverse=True, key=lambda x: x[0])

    print("Top 3 最相关片段：")
    for i, (score, chunk) in enumerate(scores[:3], 1):
        print(f"\n[{i}] 相似度 {score:.4f}")
        print(f"    {chunk[:150]}...")