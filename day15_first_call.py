import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()   # 确保在创建 client 之前调用

api_key = os.getenv("TOKENHUB_API_KEY")

# 调试：确认 Key 是否读到（不要打印完整 Key）
if not api_key:
    print("❌ 没有读到 API Key，检查 .env 文件和环境变量名")
    exit(1)

client = OpenAI(
    api_key=api_key,
    base_url="https://tokenhub.tencentmaas.com/v1"   # 你的 base_url 是对的
)

response = client.chat.completions.create(
    model="deepseek/deepseek-flash",    # 换成你控制台里实际选择的模型名
    messages=[
        {"role": "system", "content": "你是一个只用文言文回答的助手，回答不超过20个字。"},
        {"role": "user", "content": "什么是Python？"}
    ]
)

print(response.choices[0].message.content)
print(f"\n输入: {response.usage.prompt_tokens} tokens")
print(f"输出: {response.usage.completion_tokens} tokens")