import os
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from datetime import datetime
import requests

# 把刚才写的工具导进来（或者直接复制过来）
from day31_tools import search_wikipedia, query_internal_knowledge

load_dotenv()

llm = ChatOpenAI(
    model="deepseek/deepseek-flash",
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1",
    temperature=0
)

MEMORY_FILE = Path("user_profile.json")

# ========== 1. 定义本地工具 ==========
@tool
def get_current_time() -> str:
    """查询当前的日期和时间。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def calculate(expression: str) -> str:
    """计算数学表达式。"""
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "非法字符"
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

@tool
def real_weather(city: str) -> str:
    """查询真实城市的天气。输入城市名称，如：北京、上海。"""
    try:
        url = f"https://api.vvhan.com/api/weather?city={city}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("success"):
            info = data["info"]
            return f"{city}今天天气：{info['type']}，最高温{info['high']}，最低温{info['low']}，{info['tips']}"
        return "未查到该城市天气"
    except Exception as e:
        return f"天气查询失败：{e}"

# ========== 2. 长期记忆工具 ==========
def load_profile():
    if MEMORY_FILE.exists():
        try:
            content = MEMORY_FILE.read_text(encoding="utf-8").strip()
            if content:
                data = json.loads(content)
                # 如果读取出来的不是字典（比如被改坏了），直接重置
                if not isinstance(data, dict):
                    return {"facts": []}
                # 如果是旧版本（没有 facts），把旧键值对转成字符串放进 facts
                if "facts" not in data:
                    new_facts = [f"{k}: {v}" for k, v in data.items()]
                    return {"facts": new_facts}
                return data
        except Exception as e:
            print(f"⚠️ 档案读取失败: {e}")
    return {"facts": []}   # 默认返回干净的列表

def save_profile(profile):
    MEMORY_FILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")

@tool
def remember_fact(fact: str) -> str:
    """记住关于用户的一条事实。直接把完整事实传进来，比如：'用户叫张三' 或 '用户喜欢喝茶'。"""
    profile = load_profile()
    # 用列表来存所有的 fact
    if "facts" not in profile:
        profile["facts"] = []
    
    # 避免重复存一模一样的
    if fact not in profile["facts"]:
        profile["facts"].append(fact)
        save_profile(profile)
        return f"已记住：{fact}"
    return f"这个信息已经记过了：{fact}"

@tool
def forget_fact(fact:str) -> str:
    """忘记关于用户的一个长期事实。传入要忘记的完整内容）。"""
    profile = load_profile()
    if "facts" in profile and fact in profile["facts"]:
        profile["facts"].remove(fact)
        save_profile(profile)
        return f"已成功忘记：{fact}"
    return f"档案里没有'{fact}'这个信息。"

@tool
def forget_all_facts() -> str:
    """忘记关于用户的所有信息。当用户明确要求清空记忆时使用。"""
    save_profile({})
    return "已彻底清空所有记忆。"

# 汇总所有工具（现在有 8 个）
tools = [
    get_current_time, 
    calculate, 
    search_wikipedia, 
    query_internal_knowledge,
    real_weather,
    remember_fact,
    forget_fact,
    forget_all_facts
    ]

# ========== 3. 核心交互循环 ==========
def chat_loop():
    print("欢迎使用全能智能助手。输入 'q' 退出，'clear' 清空对话历史。")
    
    # ★ 短期记忆容器
    messages = []  
    
    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() == "q":
            break
        if user_input.lower() == "clear":
            messages = []
            print("（短期对话历史已清空，但长期记忆还在）")
            continue
        if not user_input:
            continue
     
     # ★ 读取长期记忆，拼入 System Prompt
        profile = load_profile()
        memory_context = "【用户档案】\n"
        if profile and "facts" in profile and profile["facts"]:
            for fact in profile["facts"]:
                memory_context += f"- {fact}\n"
        else:
            memory_context += "（暂无已知信息）\n"

        system_prompt = f"""你是一个全能助手。你可以:
1. 查时间、做计算
2. 搜索维基百科（常识、人物、历史）
3. 查询企业内部知识库（公司规定、内部文档）
4. 记忆功能

请参考以下用户档案来回答问题：
{memory_context}

规则：
1. 如果用户告诉你新的个人信息，请调用 remember_fact。
2. 如果用户让你忘掉某事，请调用 forget_fact。
3. 如果不需要工具，直接回答。
"""

        # ★ 每次动态创建 Agent（带上最新的 System Prompt）
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt
        )

        # ★ 把用户输入加入短期记忆
        messages.append(("user", user_input))

        try:
            # 传入完整短期历史
            result = agent.invoke({"messages": messages})
            
            # 输出结果
            print(f"AI: {result['messages'][-1].content}")
            
            # ★ 把 Agent 的完整中间状态（包括工具调用）覆盖回短期记忆
            messages = result["messages"]
            
        except Exception as e:
            print(f"出错: {e}")

if __name__ == "__main__":
    chat_loop()