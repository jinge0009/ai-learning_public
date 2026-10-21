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

# ========== 历史截断 ==========
def trim_messages(messages, max_turns=10):
    """保留 system + 最近 max_turns 轮（从 user 开始算）"""
    if len(messages) <= 1:
        return messages

    system = messages[0]
    rest = messages[1:]

    # 找到所有 user 消息的位置
    user_indices = [
        i for i, m in enumerate(rest)
        if isinstance(m, dict) and m.get("role") == "user"
    ]

    if len(user_indices) <= max_turns:
        return [system] + rest

    start = user_indices[-max_turns]
    return [system] + rest[start:]

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
            "name": "get_current_time",
            "description": "查询当前时间",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

# ========== 工具函数 ==========
def get_weather(city: str) -> str:
    data = {"北京": "晴，25°C", "上海": "多云，28°C", "广州": "阵雨，30°C"}
    return data.get(city, f"暂无{city}的天气数据")

def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ========== 主对话循环 ==========
def chat_with_tools():
    messages = [
        {"role": "system", "content": "你是一个友好的助手，回答简洁。需要实时信息时调用工具。"}
    ]

    print("输入 q 退出\n")

    while True:
        user_input = input("你: ")
        if user_input.lower() == "q":
            print("再见")
            break

        messages.append({"role": "user", "content": user_input})

        messages = trim_messages(messages, max_turns=10)#历史截断

        # 循环处理工具调用，直到模型给出最终回复
        while True:
            response = client.chat.completions.create(
                model="deepseek/deepseek-flash",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            message = response.choices[0].message
            messages.append(message)

            # 没有工具调用，结束
            if not message.tool_calls:
                print(f"AI: {message.content}\n")
                print(f"[历史 {len(messages)} 条 | 输入 {response.usage.prompt_tokens} tokens]")
                break

            # 执行工具
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                print(f"[调用工具] {function_name}({arguments})")

                if function_name == "get_weather":
                    result = get_weather(arguments["city"])
                elif function_name == "get_current_time":
                    result = get_current_time()
                else:
                    result = f"未知函数: {function_name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
            # 循环继续，让模型基于工具结果生成回答

chat_with_tools()