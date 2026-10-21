import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.prompts import PromptTemplate

load_dotenv()

# ========== 1. 初始化模型 ==========
llm = ChatOpenAI(
    model="deepseek/deepseek-flash",
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1",
    temperature=0
)

# ========== 2. 定义工具 ==========
@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气。输入应该是城市名称，如：北京、上海。"""
    data = {"北京": "晴，25°C", "上海": "多云，28°C"}
    return data.get(city, f"未知城市：{city}")

@tool
def calculate(expression: str) -> str:
    """计算数学表达式，输入应该是字符串形式的算式，如：3+5*2。"""
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "表达式包含非法字符"
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

@tool
def get_current_time() -> str:
    """查询当前的日期和时间，不需要任何输入参数。"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def search_document(query: str) -> str:
    """在企业知识库中搜索相关文档内容。"""
    return f"找到关于【{query}】的文档：公司年假政策规定，入职满1年享有5天年假。"

# 注册工具列表
tools = [get_weather, calculate, get_current_time,search_document]

# ========== 3. 创建并运行 Agent (新版) ==========
# 创建 Agent
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="你是一个智能助手，可以使用工具来回答问题。"
)

# 运行 Agent
if __name__ == "__main__":
    print("=== 测试1：需要多步工具 ===")
    # 新版调用方式：传入 messages 列表
    result1 = agent.invoke({
        "messages": [("user", "北京天气怎么样？帮我算一下 25 + 28 是多少？现在几点了？")]
    })
    # 最终输出在 messages 的最后一条
    print("\n最终输出:", result1["messages"][-1].content)
    
    print("\n\n=== 测试2：闲聊 ===")
    result2 = agent.invoke({
        "messages": [("user", "你好，请用一句话介绍你自己。")]
    })
    print("\n最终输出:", result2["messages"][-1].content)

    print("\n\n=== 测试3：调用知识库工具 ===")
    result3 = agent.invoke({
        "messages": [("user", "我们公司的年假政策是什么？")]
    })
    print("\n最终输出:", result3["messages"][-1].content)