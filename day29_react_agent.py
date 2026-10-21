import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

load_dotenv()

client = OpenAI(
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1"
)

# ========== 1. 定义工具 ==========
def get_weather(city: str) -> str:
    data = {"北京": "晴，25°C", "上海": "多云，28°C"}
    return data.get(city, f"未知城市：{city}")

def calculate(expression: str) -> str:
    try:
        # 安全评估（仅限数字和运算符）
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "表达式包含非法字符"
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 工具注册表
TOOLS = {
    "get_weather": get_weather,
    "calculate": calculate,
    "get_current_time":get_current_time,
}

# ========== 2. 定义 System Prompt（核心） ==========
SYSTEM_PROMPT = """你是一个智能助手，可以使用工具来回答问题。在输出 Final Answer 之前，必须用一句话总结你做了哪些操作。

可用工具：
1. get_weather(city: str) - 查询城市天气
2. calculate(expression: str) - 计算数学表达式
3. get_current_time() - 查询时间

你必须严格按以下格式输出，每次只输出一步：
Thought: 你的思考过程
Action: 工具名（必须是上面列出的工具之一）
Action Input: 工具的 JSON 参数

或者，如果你已经知道最终答案，直接输出：
Thought: 我已经知道答案了
Final Answer: 你的最终回答

注意：Action 和 Final Answer 不能同时出现。"""

# ========== 3. Agent 循环 ==========
def run_agent(user_input: str, max_steps: int = 5):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    print(f"\n用户: {user_input}\n" + "="*40)

    for step in range(max_steps):
        # 1. 调用大模型
        response = client.chat.completions.create(
            model="deepseek/deepseek-flash",
            messages=messages,
            stop=["Observation:"]  # 阻止模型自己编造 Observation
        )
        reply = response.choices[0].message.content.strip()
        print(reply)

        # 2. 把模型输出加入历史
        messages.append({"role": "assistant", "content": reply})

        # 3. 判断是否结束
        if "Final Answer:" in reply:
            print("\n" + "="*40)
            break

        # 4. 解析 Action
        if "Action:" in reply and "Action Input:" in reply:
            try:
                # 简单解析（实际项目用正则或更严谨的解析）
                action = reply.split("Action:")[1].split("\n")[0].strip()
                action_input_str = reply.split("Action Input:")[1].strip()

                # 执行工具
                if action in TOOLS:
                    args = json.loads(action_input_str)
                    # 展开字典参数
                    observation = TOOLS[action](**args)
                else:
                    observation = f"错误：找不到工具 {action}"

            except Exception as e:
                observation = f"工具执行失败: {e}"

            # 5. 把 Observation 塞回历史
            obs_text = f"Observation: {observation}"
            print(obs_text + "\n" + "-"*40)
            messages.append({"role": "user", "content": obs_text})

        else:
            print("\n[警告] 模型未按格式输出，可能陷入了死循环。")
            break

    else:
        print(f"\n[警告] 超过最大步数 {max_steps}，强制停止。")

if __name__ == "__main__":
    # 测试1：需要工具
    run_agent("北京和上海的天气怎么样？帮我算一下 25 + 28 是多少。现在几点了？")
    
    # 测试2：不需要工具
    run_agent("你好，请用一句话介绍你自己。")