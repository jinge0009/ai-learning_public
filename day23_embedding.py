import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

def get_embedding(text: str) -> list[float]:
    """把文本转成向量"""
    response = client.embeddings.create(
        model="kinfra-text-embedding-0.6b",    # 模型名以控制台为准
        input=text,
        encoding_format="float" 
    )
    return response.data[0].embedding


if __name__ == "__main__":
    texts = [
        "我喜欢猫",
        "我爱猫咪",
        "今天下雨了"
    ]

    embeddings = [get_embedding(t) for t in texts]
    print(f"向量维度: {len(embeddings[0])}")
    print(f"前5个数字: {embeddings[0][:5]}")