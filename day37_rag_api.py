import os
import json
from pathlib import Path
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
import traceback
from sentence_transformers import CrossEncoder
from sqlalchemy.orm import Session

from day22_load import load_document
from day23_split import split_text

# ★ 新增数据库相关导入
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
HISTORY_FILE = Path("qa_history.json")

app = FastAPI(title="RAG 知识库 API", version="2.0")

# ★ 启动时自动在数据库中建表
models.Base.metadata.create_all(bind=engine)
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
    text = load_document(file_path)
    chunks = split_text(text, chunk_size=200, chunk_overlap=30)
    if not chunks:
        raise ValueError(
            "文档内容为空。可能原因："
            "1) PDF 是扫描件（图片），需要 OCR 提取；"
            "2) 文档没有文字内容"
        )

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

    #阈值过滤
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

async def rag_stream_generator(question: str, coarse_k: int = 20, fine_k: int = 3, rerank_threshold: float = 0.5, vector_threshold: float = 0.3):
    """RAG 流式生成器"""
    # 1. 检索阶段（和原来一样）
    results = collection.query(query_texts=[question], n_results=coarse_k)
    docs = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    if not docs:
        yield f"data: {json.dumps({'text': '知识库为空，请先上传文档'}, ensure_ascii=False)}\n\n"
        return

    # Rerank 精排
    pairs = [[question, doc] for doc in docs]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(docs, distances, metadatas, scores), key=lambda x: x[3], reverse=True)[:fine_k]

    # 阈值过滤
    filtered = [
        (doc, dist, meta, float(score))
        for doc, dist, meta, score in ranked
        if float(score) >= rerank_threshold and (1 - dist) >= vector_threshold
    ]

    if not filtered:
        yield f"data: {json.dumps({'text': '根据提供的资料，我无法回答这个问题'}, ensure_ascii=False)}\n\n"
        return

    # 拼接上下文
    filtered_docs = [f[0] for f in filtered]
    context = "\n\n---\n\n".join(filtered_docs)

    prompt = f"""你是一个知识库问答助手。请根据下面提供的资料回答用户问题。

资料：
{context}

用户问题：{question}

回答规则：
1. 只根据上面的资料回答，不要编造
2. 如果资料中没有相关信息，回答"根据提供的资料，我无法回答这个问题"
3. 回答简洁明了"""

    # 2. 生成阶段（开启 stream=True）
    full_answer = "" # ★ 新增：用来收集完整的回答
    try:
        response = client_ai.chat.completions.create(
            model="deepseek/deepseek-flash",
            messages=[{"role": "user", "content": prompt}],
            stream=True  # ★ 开启流式
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_answer += text  # ★ 把碎片拼起来
                # 将每个 chunk 封装成 SSE 格式发给前端
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"

        # 3. 在流式结束的最后，存入数据库，把来源信息发给前端
        db_record = models.ChatHistory(
            user_id="web_user",
            question=question,
            answer=full_answer
        )
        db.add(db_record)
        db.commit()

        sources = [
            {
                "source": meta.get("source"),
                "index": meta.get("index"),
                "rerank_score": round(float(score), 4)
            }
            for doc, dist, meta, score in filtered
        ]
        # 用特殊的 type 标记这是来源数据，而不是普通文本
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'text': f'生成出错: {e}'}, ensure_ascii=False)}\n\n"

async def save_and_index(file: UploadFile) -> dict:
    """保存单个文件并入库"""
    filename = file.filename
    if not filename:
        raise HTTPException(400, "文件缺少文件名")

    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            400,
            f"不支持的文件类型：{suffix or '(无扩展名)'}，"
            f"只允许 {', '.join(sorted(ALLOWED_SUFFIXES))}"
        )

    file_path = UPLOAD_DIR / filename
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        chunk_count = index_document(str(file_path), filename)
    except Exception as e:
        raise HTTPException(500, f"文档处理失败：{e}")

    return {"file": filename, "size": len(content), "chunks": chunk_count}

def save_history():
    """保存历史到文件"""
    HISTORY_FILE.write_text(
        json.dumps(qa_history, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


# ========== 4. API 路由 ==========
@app.get("/")
def root():
    return {"message": "RAG 知识库 API", "docs": "/docs"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传单个文档"""
    try:
        result = await save_and_index(file)
        return {"message": "上传成功", **result}
    except HTTPException:
        raise    # 已知错误，正常返回
    except Exception as e:
        traceback.print_exc()    # ★ 强制打印堆栈到终端
        raise HTTPException(
            status_code=500,
            detail=f"内部错误：{type(e).__name__}: {e}"
        )


@app.post("/upload-batch")
async def upload_batch(files: list[UploadFile] = File(...)):
    """批量上传文档"""
    results = [await save_and_index(f) for f in files]
    return {"total": len(results), "results": results}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """提问，返回 RAG 回答并存入数据库"""
    if not req.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="问题不能为空"
        )
    result = rag_query(
        req.question,
        req.coarse_k,
        req.fine_k,
        req.rerank_threshold,
        req.vector_threshold
    )
    
    # ★ 存入数据库
    db_record = models.ChatHistory(
        user_id="web_user",
        question=req.question,
        answer=result["answer"]
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return result

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    """查询最近10条历史"""
    records = db.query(models.ChatHistory).order_by(models.ChatHistory.created_at.desc()).limit(10).all()
    
    history_list = [
        {
            "question": r.question, 
            "answer": r.answer, 
            "time": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } 
        for r in records
    ]
    return {"total": len(history_list), "history": history_list}

@app.delete("/history")
def clear_history(db: Session = Depends(get_db)):
    """清空历史"""
    db.query(models.ChatHistory).delete()
    db.commit()
    return {"message": "历史记录已从数据库清空"}

@app.get("/documents")
def list_documents():
    """查询所有文档"""
    results = collection.get()
    sources = {meta.get("source") for meta in results["metadatas"] if meta.get("source")}
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
        raise HTTPException(404, f"删除失败：{e}")

    # 顺便删本地文件
    file_path = UPLOAD_DIR / name
    if file_path.exists():
        file_path.unlink()

@app.post("/chat_stream")
async def chat_stream(req: ChatRequest, db: Session = Depends(get_db)): # ★
    """流式 RAG 问答接口"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    return StreamingResponse(
        rag_stream_generator(
            req.question, 
            db,  # ★ 把 db 传给生成器
            req.coarse_k, 
            req.fine_k, 
            req.rerank_threshold, 
            req.vector_threshold
        ),
        media_type="text/event-stream"
    )