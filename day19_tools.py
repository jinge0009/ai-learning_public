import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

# 定义工具（告诉模型有哪些函数可用）
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的天气",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "计算数学表达式，支持加减乘除和括号",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如：3+5*2"
                }
            },
            "required": ["expression"]
        }
    }
}
]

def get_weather(city: str) -> str:
    """模拟天气查询，实际项目会调真实 API"""
    weather_data = {
        "北京": "晴，25°C，微风",
        "上海": "多云，28°C，东南风3级",
        "广州": "阵雨，30°C，湿度80%"
    }
    return weather_data.get(city, f"暂无{city}的天气数据")

def calculate(expression: str) -> str:
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "表达式包含非法字符"
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算失败: {e}"

def chat_with_tools(user_input: str):
    # 1. 第一轮：用户提问 + 工具定义
    messages = [{"role": "user", "content": user_input}]

    response = client.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    # 2. 如果模型没有调用工具，直接返回
    if not message.tool_calls:
        return message.content

    # 3. 模型要调用工具，把这条 assistant 消息加入历史
    messages.append(message)

    # 4. 逐个执行工具调用
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        print(f"[调用工具] {function_name}({arguments})")

        # 根据函数名执行对应的函数
        if function_name == "get_weather":
            result = get_weather(arguments["city"])
        elif function_name == "calculate":
            result = calculate(arguments["expression"])
        else:
            result = f"未知函数: {function_name}"

        # 5. 把工具结果加入历史
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })

    # 6. 第二轮：把工具结果发给模型，让它生成最终回答
    final_response = client.chat.completions.create(
        model="deepseek/deepseek-flash",
        messages=messages,
        tools=tools
    )

    return final_response.choices[0].message.content

# 测试
print(chat_with_tools("帮我算一下 123 * 456"))
print(chat_with_tools("北京天气怎么样？"))
print(chat_with_tools("上海和北京哪个更热？"))    # 触发两次天气调用