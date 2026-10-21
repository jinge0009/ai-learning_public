import os
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

# 对比测试
print("=== 无约束 ===")
print(ask("给我讲个故事", system="你是一个助手"))

print("\n=== 有约束 ===")
print(ask("给我讲个故事", system="""你是一个儿童故事作家。
要求：
- 故事主角是动物
- 长度不超过100字
- 结尾有一句道理
- 适合5岁小孩听"""))