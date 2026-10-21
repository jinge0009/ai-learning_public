import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client_openai = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

class TencentEmbedding(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        response = client_openai.embeddings.create(
            model="kinfra-text-embedding-0.6b",
            input=list(input),
            encoding_format="float"
        )
        return [item.embedding for item in response.data]

client = chromadb.PersistentClient(path="./chroma_db")

# 删除旧集合并重建（测试用）
try:
    client.delete_collection("my_docs")
except:
    pass

collection = client.create_collection(
    name="my_docs",
    embedding_function=TencentEmbedding()
)

# ========== 增 ==========
collection.add(
    ids=["doc1", "doc2", "doc3"],
    documents=[
        "FastAPI 是一个现代 Python Web 框架",
        "RAG 是检索增强生成技术",
        "今天天气很好"
    ],
    metadatas=[
        {"source": "tech", "topic": "web"},
        {"source": "tech", "topic": "ai"},
        {"source": "life", "topic": "weather"}
    ]
)
print(f"添加完成，共 {collection.count()} 条\n")

# ========== 查 ==========
results = collection.query(
    query_texts=["什么是 FastAPI"],
    n_results=2
)
print("查询「什么是 FastAPI」：")
for i, doc in enumerate(results["documents"][0]):
    print(f"  {i+1}. {doc}")
    print(f"     距离: {results['distances'][0][i]:.4f}")
    print(f"     元数据: {results['metadatas'][0][i]}")

# ========== 按元数据过滤 ==========
print("\n按 source=tech 过滤：")
results = collection.query(
    query_texts=["技术"],
    n_results=10,
    where={"source": "tech"}
)
for doc in results["documents"][0]:
    print(f"  - {doc}")

# ========== 删 ==========
collection.delete(ids=["doc3"])
print(f"\n删除 doc3 后，共 {collection.count()} 条")