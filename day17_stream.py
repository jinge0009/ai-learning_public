import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

stream = client.chat.completions.create(
    model="deepseek/deepseek-flash",
    messages=[
        {"role": "system", "content": "你是一个友好的助手。"},
        {"role": "user", "content": "用300字介绍一下Python的历史。"}
    ],
    stream=True    # 关键参数
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)

print()    # 最后换行