import os
import shutil
from pathlib import Path
from typing import Optional
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from openai import OpenAI
from sentence_transformers import CrossEncoder

from day22_load import load_document
from day23_split import split_text

load_dotenv()

# ========== 1. 初始化 ==========
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
base = Path("./local_models/models")
model_dirs = list(base.glob("BAAI--bge-reranker-base/snapshots/*"))
if not model_dirs:
    raise FileNotFoundError(
        "Rerank 模型未下载。请先运行：\n"
        "  pip install modelscope\n"
        "  python download_model.py"
    )
model_path = str(model_dirs[0])
reranker = CrossEncoder(model_path)
print(f"加载完成: {model_path}\n")

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="rag_api",
    embedding_function=TencentEmbedding(),
    metadata={"hnsw:space": "cosine"}
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="RAG 知识库 API", version="1.0")

# ========== 2. Pydantic 模型 ==========
class ChatRequest(BaseModel):
    question: str
    coarse_k: int = 20
    fine_k: int = 3
    rerank_threshold: float = 0.5      # Rerank 分数阈值
    vector_threshold: float = 0.3      # 向量相似度阈值

class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]

# ========== 3. 工具函数 ==========
def index_document(file_path: str, source_name: str) -> int:
    """加载、切分、入库，返回 chunk 数量"""
    text = load_document(file_path)
    chunks = split_text(text, chunk_size=200, chunk_overlap=30)

    if not chunks:
        raise ValueError("文档内容为空")

    # 删除该文档的旧数据
    try:
        collection.delete(where={"source": source_name})
    except Exception:
        pass

    # 存入
    collection.add(
        ids=[f"{source_name}_chunk_{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"source": source_name, "index": i} for i in range(len(chunks))]
    )
    return len(chunks)


def rag_query(question: str, coarse_k: int = 20, fine_k: int = 3, rerank_threshold: float = 0.5, vector_threshold: float = 0.3) -> dict:
    """RAG 问答核心"""
    results = collection.query(
        query_texts=[question],
        n_results=coarse_k
    )

    docs = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    if not docs:
        return {"answer": "知识库为空，请先上传文档", "sources": []}

    #Rerank 阶段
    pairs = [[question, doc] for doc in docs]
    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(docs, distances, metadatas, scores),
        key=lambda x: x[3],
        reverse=True
    )[:fine_k]

    # 阈值过滤
    filtered = [
        (doc, dist, meta, float(score))
        for doc, dist, meta, score in ranked
        if float(score) >= rerank_threshold and (1 - dist) >= vector_threshold
    ]

    if not filtered:
        return {"answer": "根据提供的资料，我无法回答这个问题", "sources": []}

    docs = [f[0] for f in filtered]
    distances = [f[1] for f in filtered]
    metadatas = [f[2] for f in filtered]
    rerank_scores = [f[3] for f in filtered]

    context = "\n\n---\n\n".join(docs)

    prompt = f"""你是一个知识库问答助手。请根据下面提供的资料回答用户问题。

资料：
{context}

用户问题：{question}

回答规则：
1. 只根据上面的资料回答，不要编造
2. 如果资料中没有相关信息，回答"根据提供的资料，我无法回答这个问题"
3. 回答简洁明了"""

    response = client_ai.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content

    sources = [
        {
        "source": meta.get("source"),
        "index": meta.get("index"),
        "rerank_score": round(score, 4),
        "vector_relevance": round(1 - dist, 3),
        "preview": doc[:100]
        }
        for doc, dist, meta, score in zip(docs, distances, metadatas, rerank_scores)
    ]   

    return {"answer": answer, "sources": sources}


# ========== 4. API 路由 ==========
@app.get("/")
def root():
    return {"message": "RAG 知识库 API", "docs": "/docs"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档，自动入库"""
    # 类型检查
    allowed = [".pdf", ".docx", ".txt", ".md"]
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型：{suffix}，只允许 {allowed}"
        )

    # 保存文件
    file_path = UPLOAD_DIR / file.filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 入库
    try:
        chunk_count = index_document(str(file_path), file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败：{e}"
        )

    return {
        "message": "上传成功",
        "file_name": file.filename,
        "size": len(content),
        "chunks": chunk_count
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """提问，返回 RAG 回答"""
    if not req.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="问题不能为空"
        )
    return rag_query(
    req.question,
    req.coarse_k,
    req.fine_k,
    req.rerank_threshold,
    req.vector_threshold
)


@app.get("/documents")
def list_documents():
    """查看已上传的文档"""
    results = collection.get()
    sources = set()
    for meta in results["metadatas"]:
        sources.add(meta.get("source"))
    return {
        "total_chunks": collection.count(),
        "documents": sorted(sources)
    }


@app.delete("/documents/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(name: str):
    """删除指定文档的所有 chunk"""
    try:
        collection.delete(where={"source": name})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"删除失败：{e}"
        )

    # 顺便删本地文件
    file_path = UPLOAD_DIR / name
    if file_path.exists():
        file_path.unlink()