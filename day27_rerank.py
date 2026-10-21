import os
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import CrossEncoder

load_dotenv()

client_ai = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

class TencentEmbedding(EmbeddingFunction):
    def __init__(self):
        pass
    def __call__(self, input: Documents) -> Embeddings:
        response = client_ai.embeddings.create(
            model="kinfra-text-embedding-0.6b",
            input=list(input),
            encoding_format="float"
        )
        return [item.embedding for item in response.data]

print("加载 Rerank 模型...")
reranker = CrossEncoder("./local_models/models/BAAI--bge-reranker-base/snapshots/master")
print("加载完成\n")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="rerank_demo",
    embedding_function=TencentEmbedding(),
    metadata={"hnsw:space": "cosine"}
)


def two_stage_retrieve(question: str, coarse_k: int = 20, fine_k: int = 3):
    results = collection.query(query_texts=[question], n_results=coarse_k)
    docs = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    if not docs:
        return []

    pairs = [[question, doc] for doc in docs]
    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(docs, distances, metadatas, scores),
        key=lambda x: x[3],
        reverse=True
    )[:fine_k]

    return [
        {
            "doc": doc,
            "distance": dist,
            "meta": meta,
            "rerank_score": float(score)
        }
        for doc, dist, meta, score in ranked
    ]


if __name__ == "__main__":
    # 添加测试数据
    test_docs = [
        "FastAPI 是一个现代、高性能的 Python Web 框架，基于标准 Python 类型提示构建。",
        "RAG 是检索增强生成技术，让大模型基于外部知识库回答。",
        "Chroma 是一个轻量级的向量数据库，适合本地开发。",
        "Python 是一门解释型编程语言，语法简洁。",
        "Rerank 是两阶段检索的第二阶段，用交叉编码器精排。",
        "向量数据库用于存储和检索高维向量。",
        "Embedding 把文本转成向量，语义相近的向量距离近。",
        "大模型有上下文长度限制，不能一次处理整本书。",
        "RAG 解决了模型知识过时和不知道私有数据的问题。",
        "Chunk 是文档切分后的小块，是检索的基本单位。"
    ]

    try:
        chroma_client.delete_collection("rerank_demo")
    except:
        pass

    collection = chroma_client.create_collection(
        name="rerank_demo",
        embedding_function=TencentEmbedding(),
        metadata={"hnsw:space": "cosine"}
    )

    collection.add(
        ids=[f"doc_{i}" for i in range(len(test_docs))],
        documents=test_docs,
        metadatas=[{"source": "test", "index": i} for i in range(len(test_docs))]
    )
    print(f"已添加 {collection.count()} 条数据\n")

    question = "什么是 FastAPI？"
    print(f"问题：{question}\n")

    results = two_stage_retrieve(question)
    print(f"精排后 Top {len(results)}：")
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] Rerank 分数: {r['rerank_score']:.4f}")
        print(f"    向量距离: {r['distance']:.4f}")
        print(f"    内容: {r['doc'][:80]}...")

if __name__ == "__main__":
    questions = [
    "什么是 FastAPI？",
    "RAG 解决了什么问题？",
    "Embedding 是什么？",
    "Chroma 有什么用？"
]

for q in questions:
    print(f"\n{'='*60}")
    print(f"问题：{q}")
    print('='*60)
    for i, r in enumerate(two_stage_retrieve(q), 1):
        print(f"[{i}] Rerank {r['rerank_score']:.4f} | {r['doc'][:60]}...")