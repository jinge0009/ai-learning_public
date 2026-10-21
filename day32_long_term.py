import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent

load_dotenv()

llm = ChatOpenAI(
    model="deepseek/deepseek-flash",
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1",
)

MEMORY_FILE = Path("user_profile.json")

# ========== 1. 定义长期记忆的读写工具 ==========
def load_profile():
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    return {}

def save_profile(profile):
    MEMORY_FILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")

@tool
def remember_fact(key: str, value: str) -> str:
    """记住关于用户的一个长期事实。key 是属性名（如：姓名、爱好、职业），value 是属性值。"""
    profile = load_profile()
    profile[key] = value
    save_profile(profile)
    return f"已成功记住：{key} 是 {value}"

@tool
def forget_fact(key:str) -> str:
    """忘记关于用户的一个长期事实。key是属性名（如：职业、爱好）。"""
    profile = load_profile()
    if key in profile:
        del profile[key]
        save_profile(profile)
        return f"已成功忘记：{key}"
    else:
        return f"档案里本来就没有{key}这个信息。"

tools = [remember_fact,forget_fact]

def chat_long_term():
    print("欢迎使用长期记忆助手。你可以告诉我你的名字或爱好。输入 'q' 退出。")
    
    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() == "q":
            break
        if not user_input:
            continue

        # ★ 核心：每次对话前，读取长期记忆，动态拼进 System Prompt
        profile = load_profile()
        memory_context = "【用户档案】\n"
        if profile:
            for k, v in profile.items():
                memory_context += f"- {k}: {v}\n"
        else:
            memory_context += "（暂无已知信息）\n"

        system_prompt = f"""你是一个贴心的私人助手。请根据用户档案来回答问题。
{memory_context}

如果用户让你记住什么，请使用 remember_fact 工具。
当用户提到自己的信息时，也可以在闲聊中顺带回答。
"""

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt
        )

        result = agent.invoke({"messages": [("user", user_input)]})
        print(f"AI: {result['messages'][-1].content}")

if __name__ == "__main__":
    chat_long_term()