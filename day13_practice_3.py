#任务三：文本统计API（总字符数，总行数，总次数（按空格切分））
from fastapi import FastAPI, UploadFile, File, HTTPException, status

app = FastAPI(title="文本统计示例")

@app.post("/text_stats")
async def text_stats(file: UploadFile = File(...)):
    # 检查文件类型
    if file.content_type != "text/plain":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只允许上传.txt文件"
        )
    
    # 读取文件内容
    content = await file.read()
    text = content.decode("utf-8")
    
    # 统计总字符数、总行数、总次数（按空格切分）
    total_chars = len(text)
    total_lines = len(text.splitlines())
    total_words = len(text.split())
    
    return {
        "total_chars": total_chars,
        "total_lines": total_lines,
        "total_words": total_words
    }