import os
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

app = FastAPI(title="流式 API")

class ChatRequest(BaseModel):
    question: str

# 生成器函数：不断产出数据
async def stream_generator(question: str):
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-flash",
            messages=[
                {"role": "system", "content": "你是一个友好的AI助手，回答简洁。"},
                {"role": "user", "content": question}
            ],
            stream=True
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                # SSE (Server-Sent Events) 格式：data: 内容\n\n
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.post("/chat_stream")
async def chat_stream(req: ChatRequest):
    # 返回流式响应
    return StreamingResponse(
        stream_generator(req.question),
        media_type="text/event-stream"
    )