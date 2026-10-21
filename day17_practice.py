import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

def ask_stream(question: str, system: str = "你是一个友好的助手") -> str:
    """流式调用，实时打印，最后返回完整文本"""
    stream = client.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question}
        ],
        stream=True,
        stream_options={"include_usage": True}    # 让最后一个chunk带用量
    )

    full_reply = ""
    prompt_tokens = 0
    completion_tokens = 0

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            full_reply += content
        # 最后一个 chunk 会带 usage
        if chunk.usage:
            prompt_tokens = chunk.usage.prompt_tokens
            completion_tokens = chunk.usage.completion_tokens

    print()    # 结束后换行
    print(f"[输入 {prompt_tokens} tokens | 输出 {completion_tokens} tokens]")
    return full_reply

def chat():
    print("输入 q 退出\n")
    while True:
        question = input("你: ")
        if question.lower() == "q":
            print("再见")
            break
        print("AI: ", end="")
        ask_stream(question)

chat()