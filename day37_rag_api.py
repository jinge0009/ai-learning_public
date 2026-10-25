import os
import json
import redis
import hashlib
from pathlib import Path
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import traceback
from sentence_transformers import CrossEncoder
from sqlalchemy.orm import Session

from day22_load import load_document
from day23_split import split_text

from database import engine, get_db
import models

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
model_path = "/app/local_models/models/BAAI--bge-reranker-base/snapshots/master"
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
ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt", ".md"}

app = FastAPI(title="RAG 知识库 API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# ========== 2. Pydantic 模型 ==========
class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []  # ★ 新增：接收前端传来的历史
    coarse_k: int = 20
    fine_k: int = 3
    rerank_threshold: float = 0.5
    vector_threshold: float = 0.3

class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]

# ========== 3. 工具函数 ==========
def index_document(file_path: str, source_name: str) -> int:
    text = load_document(file_path)
    chunks = split_text(text, chunk_size=200, chunk_overlap=30)
    if not chunks:
        raise ValueError("文档内容为空。")
    try:
        collection.delete(where={"source": source_name})
    except Exception:
        pass
    collection.add(
        ids=[f"{source_name}_chunk_{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"source": source_name, "index": i} for i in range(len(chunks))]
    )
    return len(chunks)

async def rag_stream_generator(question: str, history: list, db: Session, cache_key: str, coarse_k: int = 20, fine_k: int = 3, rerank_threshold: float = 0.5, vector_threshold: float = 0.3):
    """RAG 流式生成器"""
    results = collection.query(query_texts=[question], n_results=coarse_k)
    docs = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    if not docs:
        yield f"data: {json.dumps({'text': '知识库为空，请先上传文档'}, ensure_ascii=False)}\n\n"
        return

    pairs = [[question, doc] for doc in docs]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(docs, distances, metadatas, scores), key=lambda x: x[3], reverse=True)[:fine_k]

    filtered = [
        (doc, dist, meta, float(score))
        for doc, dist, meta, score in ranked
        if float(score) >= rerank_threshold and (1 - dist) >= vector_threshold
    ]

    if not filtered:
        yield f"data: {json.dumps({'text': '根据提供的资料，我无法回答这个问题'}, ensure_ascii=False)}\n\n"
        return

    filtered_docs = [f[0] for f in filtered]
    context = "\n\n---\n\n".join(filtered_docs)

    # ★ 拼接多轮对话历史
    history_text = ""
    if history:
        history_text = "\n【历史对话】\n" + "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])

    prompt = f"""你是一个知识库问答助手。请根据下面提供的资料回答用户问题。
{history_text}

资料：
{context}

用户问题：{question}

回答规则：
1. 只根据上面的资料回答，不要编造
2. 如果资料中没有相关信息，回答"根据提供的资料，我无法回答这个问题"
3. 回答简洁明了"""

    full_answer = ""
    try:
        response = client_ai.chat.completions.create(
            model="deepseek/deepseek-flash",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_answer += text
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"

        # 存入数据库
        db_record = models.ChatHistory(
            user_id="web_user",
            question=question,
            answer=full_answer
        )
        db.add(db_record)
        db.commit()

        # ★ 存入 Redis 缓存
        redis_client.setex(cache_key, 86400, full_answer)

        sources = [
            {
                "source": meta.get("source"),
                "index": meta.get("index"),
                "rerank_score": round(float(score), 4),
                "content": doc[:200] # ★ 新增：把匹配到的原文前 200 个字符发给前端
            }
            for doc, dist, meta, score in filtered
        ]
        # 用特殊的 type 标记这是来源数据，而不是普通文本
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"
   
    except Exception as e:
        yield f"data: {json.dumps({'text': f'生成出错: {e}'}, ensure_ascii=False)}\n\n"

# ========== 4. API 路由 ==========
@app.post("/chat_stream")
async def chat_stream(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    # 1. 生成缓存 Key（★ 多轮对话时，同一个问题不能直接命中缓存，因为上下文可能变了）
    # 简单处理：把历史和问题一起 Hash
    hash_str = req.question + json.dumps(req.history, ensure_ascii=False)
    question_hash = hashlib.md5(hash_str.encode()).hexdigest()
    cache_key = f"chat:{question_hash}"

    # 2. 查缓存
    cached_answer = redis_client.get(cache_key)
    if cached_answer:
        print(f"🔥 [缓存命中] {req.question}")
        async def cached_stream():
            yield f"data: {json.dumps({'text': cached_answer.decode('utf-8')}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'sources', 'sources': []}, ensure_ascii=False)}\n\n"
        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    # 3. 未命中，走 RAG
    return StreamingResponse(
        rag_stream_generator(
            req.question, req.history, db, cache_key, 
            req.coarse_k, req.fine_k, req.rerank_threshold, req.vector_threshold
        ),
        media_type="text/event-stream"
    )

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename
    if not filename:
        raise HTTPException(400, "文件缺少文件名")
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(400, f"不支持的文件类型：{suffix}")
    file_path = UPLOAD_DIR / filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    try:
        chunk_count = index_document(str(file_path), filename)
    except Exception as e:
        raise HTTPException(500, f"文档处理失败：{e}")
    return {"message": "上传成功", "file": filename, "size": len(content), "chunks": chunk_count}

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    records = db.query(models.ChatHistory).order_by(models.ChatHistory.created_at.desc()).limit(10).all()
    return {"total": len(records), "history": [{"question": r.question, "answer": r.answer} for r in records]}

@app.delete("/documents/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(name: str):
    try:
        collection.delete(where={"source": name})
    except Exception as e:
        raise HTTPException(404, f"删除失败：{e}")
    file_path = UPLOAD_DIR / name
    if file_path.exists():
        file_path.unlink()

@app.get("/documents")
def list_documents():
    """查询所有已上传的文档列表"""
    results = collection.get()
    sources = {meta.get("source") for meta in results["metadatas"] if meta.get("source")}
    return {
        "total_chunks": collection.count(),
        "documents": sorted(sources)
    }
