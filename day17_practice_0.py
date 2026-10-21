import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

def ask_json_stream(text: str) -> str:
    stream = client.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=[
            {"role": "system", "content": "从用户文本提取姓名、年龄、城市，输出JSON，只输出JSON。"},
            {"role": "user", "content": text}
        ],
        stream=True
    )

    full = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            c = chunk.choices[0].delta.content
            print(c, end="", flush=True)
            full += c

    print()
    return full

result = ask_json_stream("我叫小明，今年18岁，住在北京")
print("\n完整JSON:", result)

data = json.loads(result)
print(f"姓名: {data['name']} | 年龄: {data['age']} | 城市: {data['city']}")