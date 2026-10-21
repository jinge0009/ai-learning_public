import os
import time
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

question = "用300字介绍Python的历史。"

print("=" * 50)
print("【非流式】")
print("=" * 50)
start = time.time()
response = client.chat.completions.create(
    model="deepseek/deepseek-flash",
    messages=[{"role": "user", "content": question}]
)
print(response.choices[0].message.content)
print(f"\n耗时: {time.time() - start:.2f} 秒")

print("\n" + "=" * 50)
print("【流式】")
print("=" * 50)
start = time.time()
stream = client.chat.completions.create(
    model="deepseek/deepseek-flash",
    messages=[{"role": "user", "content": question}],
    stream=True
)
for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)
print(f"\n耗时: {time.time() - start:.2f} 秒")