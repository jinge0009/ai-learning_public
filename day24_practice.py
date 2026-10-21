import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
import os
from dotenv import load_dotenv
from openai import OpenAI
from day22_load import load_document
from day23_split import split_text

load_dotenv()

client_openai = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

class TencentEmbedding(EmbeddingFunction):
    def __init__(self):
        pass

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

# 加载 + 切分
text = load_document("sample.pdf")
chunks = split_text(text, chunk_size=100, chunk_overlap=20)

# 存入 Chroma
collection.add(
    ids=[f"chunk_{i}" for i in range(len(chunks))],
    documents=chunks,
    metadatas=[{"source": "sample.pdf", "index": i} for i in range(len(chunks))]
)
print(f"添加完成，共 {collection.count()} 条\n")

# 查询
print("查询「什么是 FastAPI」：")
results = collection.query(
    query_texts=["什么是 FastAPI"],
    n_results=2
)
for i, doc in enumerate(results["documents"][0], 1):
    print(f"[{i}] 距离 {results['distances'][0][i-1]:.4f}")
    print(f"    {doc[:100]}...")

# 删除
collection.delete(where={"source": "sample.pdf"})
print(f"删除后剩余：{collection.count()}")