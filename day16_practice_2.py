import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

def ask(question: str, system: str) -> str:
    response = client.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

def summarize_article(text:str) -> dict:
    system = """从用户文本中提取信息,输出JSON:
{
"summary":"50字以内的摘要",
"keywords":["关键词1","关键词2","关键词3"],
"difficulty":"根据学习难度进行评级"
}
规则：
- 不存在的字段填null
- 只输出JSON,不要其他文字
- keywords是数组,3-5个关键词
- difficulty只能是"入门"、"中级"、"高级"之一"""

    reply = ask(text,system)

    reply = reply.strip()
    if reply.startswith("```"):
        reply = reply.split("\n",1)[1].rsplit("```",1)[0]

    return json.loads(reply.strip())

article = """
FastAPI 是一个现代、快速（高性能）的 Python Web 框架，
基于标准 Python 类型提示构建。它支持异步编程，
自动生成交互式 API 文档，被广泛用于构建 RESTful API 和微服务。
"""

result = summarize_article(article)

print(result)
print(type(result))
print("摘要:", result["summary"])
print("关键词:", result["keywords"])