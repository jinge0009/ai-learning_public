#任务二：文件上传API（只允许.txt和.pdf文件;文件大小限制2MB；保存时重命名）
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from datetime import datetime
from pathlib import Path

app = FastAPI(title="文件上传示例")

ALLOWED_TYPES = ["application/pdf", "text/plain"]
MAX_SIZE = 2 * 1024 * 1024  # 2MB
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 检查文件类型
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只允许上传.txt和.pdf文件"
        )
    
    # 检查文件大小
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过2MB"
        )
    # 重命名：原文件名_时间戳.后缀
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    new_name=f"{Path(file.filename).stem}_{timestamp}{Path(file.filename).suffix}"

    # 保存文件
    file_path = UPLOAD_DIR / new_name
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    return {
        "original_name": file.filename,
        "saved_name": new_name,
        "content_type": file.content_type,
        "size": len(content),
        "saved_to": str(file_path)
    }