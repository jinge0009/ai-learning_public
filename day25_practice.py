import os
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv
from openai import OpenAI
from day22_load import load_document
from day23_split import split_text

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

chroma_client = chromadb.PersistentClient(path="./chroma_db")

# ★ 关键：删除旧集合，用余弦距离重建
try:
    chroma_client.delete_collection("sample_pdf_rag")
    print("已删除旧集合")
except Exception:
    pass

collection = chroma_client.create_collection(
    name="sample_pdf_rag",
    embedding_function=TencentEmbedding(),
    metadata={"hnsw:space": "cosine"}    # ← 余弦距离
)

# 加载 + 切分 + 存入
text = load_document("sample.pdf")
chunks = split_text(text, chunk_size=100, chunk_overlap=20)

collection.add(
    ids=[f"chunk_{i}" for i in range(len(chunks))],
    documents=chunks,
    metadatas=[{"source": "sample.pdf", "index": i} for i in range(len(chunks))]
)
print(f"存入 {collection.count()} 条\n")

# ========== RAG Prompt ==========
RAG_PROMPT = """你是一个知识库问答助手。请根据下面提供的资料回答用户问题。

资料：
{context}

用户问题：{question}

回答规则：
1. 只根据上面的资料回答，不要编造
2. 如果资料中没有相关信息，回答"根据提供的资料，我无法回答这个问题"
3. 回答简洁明了"""

# ========== 核心 RAG 函数 ==========
def rag_query(question: str, top_k: int = 3, threshold: float = 0.3) -> str:
    results = collection.query(
        query_texts=[question],
        n_results=top_k
    )

    docs = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    if not docs:
        return "知识库为空"

    # 余弦距离下，相似度 = 1 - 距离
    filtered = [
        (doc, dist, meta)
        for doc, dist, meta in zip(docs, distances, metadatas)
        if 1 - dist > threshold
    ]

    if not filtered:
        return "根据提供的资料，我无法回答这个问题"

    docs = [f[0] for f in filtered]
    distances = [f[1] for f in filtered]
    metadatas = [f[2] for f in filtered]

    context = "\n\n---\n\n".join(docs)
    prompt = RAG_PROMPT.format(context=context, question=question)

    response = client_ai.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content

    answer += "\n\n【来源】"
    for i, (doc, dist, meta) in enumerate(zip(docs, distances, metadatas), 1):
        source = meta.get("source", "未知")
        answer += f"\n{i}. {source} (相关度: {1 - dist:.2f})"

    return answer


if __name__ == "__main__":
    # 先看原始距离值
    print("=" * 50)
    print("原始检索结果（余弦距离）：")
    print("=" * 50)
    for q in ["什么是 FastAPI？", "RAG 解决了什么问题？", "Python 是什么？"]:
        results = collection.query(query_texts=[q], n_results=3)
        print(f"\n问题：{q}")
        for doc, dist in zip(results["documents"][0], results["distances"][0]):
            print(f"  距离 {dist:.4f} | 相似度 {1-dist:.4f} | {doc[:40]}...")

    # RAG 问答
    print("\n" + "=" * 50)
    print("RAG 问答：")
    print("=" * 50)
    for q in ["什么是 FastAPI？", "RAG 解决了什么问题？", "Python 是什么？"]:
        print(f"\n问题：{q}")
        print(rag_query(q))