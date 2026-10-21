import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

# ========== 工具定义 ==========
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "查询当前时间",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "保存一条笔记，记录用户的重要信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "笔记内容"}
                },
                "required": ["content"]
            }
        }
    }
]

# ========== 工具函数 ==========
def get_weather(city: str) -> str:
    data = {"北京": "晴，25°C", "上海": "多云，28°C", "广州": "阵雨，30°C"}
    return data.get(city, f"暂无{city}的天气数据")

def calculate(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "表达式包含非法字符"
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算失败: {e}"

def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

notes = []
def save_note(content: str) -> str:
    notes.append(content)
    return f"已保存笔记，当前共 {len(notes)} 条"

# ========== 历史截断 ==========
def trim_messages(messages, max_turns=10):
    if len(messages) <= 1:
        return messages
    system = messages[0]
    rest = messages[1:]
    user_indices = [
        i for i, m in enumerate(rest)
        if isinstance(m, dict) and m.get("role") == "user"
    ]
    if len(user_indices) <= max_turns:
        return [system] + rest
    start = user_indices[-max_turns]
    return [system] + rest[start:]

# ========== 主流程 ==========
def chat():
    system_prompt = """你是一个智能助手，具备以下能力：
- 查询天气
- 数学计算
- 查询时间
- 保存笔记

回答规则：
- 回答简洁
- 需要实时信息时调用工具
- 用户表达重要信息时主动保存笔记
- 不要问"还需要什么帮助"
"""

    messages = [{"role": "system", "content": system_prompt}]

    print("=" * 40)
    print("AI 助手 v1.0")
    print("命令：q退出 / notes查看笔记 / clear清空历史")
    print("=" * 40 + "\n")

    while True:
        user_input = input("你: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "q":
            print("再见")
            break

        if user_input.lower() == "notes":
            if notes:
                print("笔记列表：")
                for i, n in enumerate(notes, 1):
                    print(f"  {i}. {n}")
            else:
                print("暂无笔记")
            continue

        if user_input.lower() == "clear":
            messages = [{"role": "system", "content": system_prompt}]
            print("历史已清空")
            continue

        messages.append({"role": "user", "content": user_input})
        messages = trim_messages(messages, max_turns=10)

        # 工具调用循环
        while True:
            response = client.chat.completions.create(
                model="deepseek/deepseek-flash",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            message = response.choices[0].message
            messages.append(message)

            if not message.tool_calls:
                print(f"AI: {message.content}")
                print(f"[历史 {len(messages)} 条 | tokens {response.usage.prompt_tokens}]\n")
                break

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                if name == "get_weather":
                    result = get_weather(args["city"])
                elif name == "calculate":
                    result = calculate(args["expression"])
                elif name == "get_current_time":
                    result = get_current_time()
                elif name == "save_note":
                    result = save_note(args["content"])
                else:
                    result = f"未知函数: {name}"

                print(f"[工具] {name}({args}) → {result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

if __name__ == "__main__":
    chat()