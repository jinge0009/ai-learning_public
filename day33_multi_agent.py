import os
from typing import TypedDict, Annotated, Sequence
import operator
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

llm = ChatOpenAI(
    model="deepseek/deepseek-flash",
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1",
    temperature=0
)

# ========== 1. 定义工人工具 ==========
@tool
def mock_search(query: str) -> str:
    """用于搜索行业资料。"""
    # 为了测试，我们返回模拟数据
    if "新能源" in query:
        return "2025年全球新能源汽车销量突破2000万辆，渗透率达到35%。中国品牌市占率超60%。"
    return "未找到相关数据。"

# ========== 2. 构建三个子 Agent ==========

# 研究员：只能用搜索工具
researcher_agent = create_agent(
    model=llm,
    tools=[mock_search],
    system_prompt="你是一个专业的研究员。请使用搜索工具查找资料，并简短地总结核心数据。"
)

# 撰稿人：不需要工具，只负责写
writer_agent = create_agent(
    model=llm,
    tools=[],
    system_prompt="你是一个资深撰稿人。请根据提供的资料，撰写一段 200 字左右的行业简报。"
)

# 审核员：不需要工具，只负责挑错
reviewer_agent = create_agent(
    model=llm,
    tools=[],
    system_prompt="你是一个严格的审核员。请检查文章的错别字和逻辑漏洞，如果没有问题就输出'通过'，有问题则直接修改并输出修改后的终稿。"
)

#翻译员：不需要工具，只负责翻译成英文
translator_agent = create_agent(
    model=llm,
    tools=[],
    system_prompt="你是一个严谨的翻译员。将文章翻译成英文。"
)
# ========== 3. 定义状态 (State) ==========
class AgentState(TypedDict):
    # Annotated[..., operator.add] 表示每次返回的消息会追加到列表里，而不是覆盖
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # 我们用一个变量记录当前任务由谁完成
    current_worker: str

# ========== 4. 定义节点 (Nodes) ==========
# 节点就是具体的执行逻辑，把子 Agent 包装成节点

def research_node(state: AgentState):
    print("\n--- [研究员] 正在查资料 ---")
    result = researcher_agent.invoke({"messages": state["messages"]})
    
    # 遍历寻找工具返回的真实数据 (ToolMessage)
    tool_results = [m.content for m in result["messages"] if type(m).__name__ == "ToolMessage"]
    
    if tool_results:
        # 拼接纯真实数据
        clean_data = "\n".join(tool_results)
        return {"messages": [HumanMessage(content=f"查到的原始资料：\n{clean_data}")]}
    else:
        return {"messages": [result["messages"][-1]]}

def write_node(state: AgentState):
    print("\n--- [撰稿人] 正在撰写初稿 ---")
    # 提取前面研究员的内容作为输入
    result = writer_agent.invoke({"messages": state["messages"]})
    return {"messages": [result["messages"][-1]]}

def review_node(state: AgentState):
    print("\n--- [审核员] 正在审核 ---")
    result = reviewer_agent.invoke({"messages": state["messages"]})
    return {"messages": [result["messages"][-1]]}

def translate_node(state: AgentState):
    print("\n--- [翻译员] 正在翻译 ---")
    result = translator_agent.invoke({"messages": state["messages"]})
    return {"messages": [result["messages"][-1]]}

# ========== 5. 组装图 (Graph) ==========
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("research", research_node)
workflow.add_node("write", write_node)
workflow.add_node("review", review_node)
workflow.add_node("translate",translate_node)

# 定义执行顺序（边）
workflow.set_entry_point("research")     # 从研究员开始
workflow.add_edge("research", "write")   # 研究员做完去撰稿
workflow.add_edge("write", "review")     # 撰稿人写完去审核
workflow.add_edge("review", "translate") # 审核完去翻译
workflow.add_edge("translate",END)       #翻译完结束

# 编译图，加上记忆（这样内部传递的消息不会丢）
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# ========== 6. 运行测试 ==========
if __name__ == "__main__":
    print("=== 多 Agent 协作系统启动 ===")
    user_query = "帮我查一下新能源车的最新市场数据，并写一篇短报告。"
    print(f"用户要求: {user_query}\n")

    # 初始输入
    inputs = {"messages": [HumanMessage(content=user_query)]}
    # 配置 thread_id 以使用记忆
    config = {"configurable": {"thread_id": "1"}}

    # 运行图
    for event in app.stream(inputs, config, stream_mode="values"):
        # stream_mode="values" 会把每一次节点执行完的状态打印出来
        last_message = event["messages"][-1]
        
    print("\n================ 最终结果 ================\n")
    print(last_message.content)