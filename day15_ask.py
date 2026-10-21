import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

def ask(question: str, system: str = "你是一个有用的助手") -> str:
    response = client.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    print(ask("介绍一下北京", system="你是一个导游"))
    print("---")
    print(ask("介绍一下北京", system="你是一个历史学家"))
    print("---")
    print(ask("介绍一下北京", system="你是一个美食博主"))