import os
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

# 定义几个本地小工具
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

# 汇总所有工具（现在有 4 个）
tools = [get_current_time, calculate, search_wikipedia, query_internal_knowledge,real_weather]

# 创建 Agent
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""你是一个全能的智能助手。你可以：
1. 查时间、做计算
2. 搜索维基百科（常识、人物、历史）
3. 查询企业内部知识库（公司规定、内部文档）

请你根据用户的问题，自主判断该使用哪个工具。如果知识库没有，可以尝试用维基百科搜索。"""
)

if __name__ == "__main__":
    print("=== 测试1：触发维基百科搜索 ===")
    result1 = agent.invoke({
        "messages": [("user", "帮我查一下乔布斯是谁？")]
    })
    print("\n最终输出:", result1["messages"][-1].content)

    print("\n\n=== 测试2：触发内部知识库 ===")
    result2 = agent.invoke({
        "messages": [("user", "请问公司年假有几天？")]
    })
    print("\n最终输出:", result2["messages"][-1].content)

    print("\n\n=== 测试3：多工具混合编排 ===")
    result3 = agent.invoke({
        "messages": [("user", "帮我查一下特斯拉的CEO是谁，然后算一下如果年假5天加上周末2天，一共休息几天？帮我查查杭州天气，然后算算杭州今天最高温减最低温是多少度？")]
    })
    print("\n最终输出:", result3["messages"][-1].content)
