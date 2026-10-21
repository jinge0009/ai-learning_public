import os
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client_ai = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

# ========== 自定义 Embedding ==========
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

# ========== 初始化 Chroma ==========
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="rag_demo",
    embedding_function=TencentEmbedding()
)

# ========== RAG Prompt ==========
# RAG的核心是这段Prompt
RAG_PROMPT = """你是一个知识库问答助手。请根据下面提供的资料回答用户问题。

资料：
{context}

用户问题：{question}

回答规则：
1. 只根据上面的资料回答，不要编造
2. 如果资料中没有相关信息，回答"根据提供的资料，我无法回答这个问题"
3. 回答简洁明了"""

# ========== 核心 RAG 函数 ==========
def rag_query(question: str, top_k: int = 3, show_sources: bool = True) -> str:
    # 1. 检索
    results = collection.query(
        query_texts=[question],
        n_results=top_k
    )

    docs = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    if not docs:
        return "知识库为空，请先添加文档"

    # 2. 拼接上下文
    context = "\n\n---\n\n".join(docs)

    # 3. 构建 Prompt
    prompt = RAG_PROMPT.format(context=context, question=question)

    # 4. 调用大模型
    response = client_ai.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    answer = response.choices[0].message.content

    # 5. 附加来源
    if show_sources:
        answer += "\n\n【来源】"
        for i, (doc, dist, meta) in enumerate(zip(docs, distances, metadatas), 1):
            source = meta.get("source", "未知")
            answer += f"\n{i}. {source} (相关度: {1 - dist:.2f})"

    return answer


# ========== 测试 ==========
if __name__ == "__main__":
    # 先添加一些测试数据
    test_docs = [
        "FastAPI 是一个现代、高性能的 Python Web 框架，基于标准 Python 类型提示构建。",
        "RAG 是检索增强生成技术，让大模型基于外部知识库回答。",
        "Chroma 是一个轻量级的向量数据库，适合本地开发。",
        "Python 是一门解释型编程语言，语法简洁。"
    ]
    collection.add(
        ids=[f"doc_{i}" for i in range(len(test_docs))],
        documents=test_docs,
        metadatas=[{"source": "test"} for _ in test_docs]
    )

    # 测试问答
    questions = [
        "什么是 FastAPI？",
        "RAG 是什么？",
        "今天天气怎么样？"    # 知识库没有，应该拒绝回答
    ]

    for q in questions:
        print(f"\n{'='*50}")
        print(f"问题：{q}")
        print('='*50)
        print(rag_query(q))