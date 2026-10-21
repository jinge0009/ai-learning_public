import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

load_dotenv()

llm = ChatOpenAI(
    model="deepseek/deepseek-flash",
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1",
    temperature=0
)

# ========== 1. 定义一个强大的计算器 ==========
@tool
def calculate(expression: str) -> str:
    """计算数学表达式，支持加减乘除，例如：3 * 5 + 10。"""
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "包含非法字符"
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

tools = [calculate]

# ========== 2. 创建 Agent ==========
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="你是一个严谨的数学助手，善于利用工具进行计算。"
)

# ========== 3. 交互式对话循环 ==========
def chat_loop():
    print("欢迎使用带记忆的计算助手。输入 'q' 退出，输入 'clear' 清空记忆。")
    # 这里就是我们的“记忆容器”
    messages = []  
    
    while True:
        user_input = input("\n你: ").strip()
        if user_input.lower() == "q":
            break
        if user_input.lower() == "clear":
            messages = []
            print("（记忆已清空）")
            continue
        if not user_input:
            continue

        # 把用户的话加进历史
        messages.append(("user", user_input))

        # 调用 Agent，传入包含历史的 messages
        try:
            result = agent.invoke({"messages": messages})
            
            # 获取最新回复
            final_message = result["messages"][-1]
            print(f"AI: {final_message.content}")
            
            # ★ 关键：把 Agent 产生的所有中间消息（包括 AI 回复和工具调用）存回历史
            # 这样下一轮它才知道自己刚才查了什么数据
            messages = result["messages"] 
            
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    chat_loop()