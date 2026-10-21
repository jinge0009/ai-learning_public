import os
import json
import requests
from typing import TypedDict, Annotated, Sequence
import operator
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.graph import StateGraph, END

load_dotenv()

llm = ChatOpenAI(
    model="deepseek/deepseek-flash",
    api_key=os.getenv("TOKENHUB_API_KEY"),
    base_url="https://tokenhub.tencentmaas.com/v1",
    temperature=0
)

# ========== 1. 封装 RAG 为工具 ==========
@tool
def query_internal_rag(question: str) -> str:
    """查询企业内部知识库。当你需要了解公司规定、员工手册、内部流程时，必须调用此工具。"""
    try:
        # 调用本地 Day 28 的 FastAPI 接口
        response = requests.post(
            "http://127.0.0.1:8000/chat",
            json={"question": question, "fine_k": 3},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        # 提取 RAG 的回答和来源
        answer = data.get("answer", "未获取到答案")
        if "无法回答" in answer or "为空" in answer:
            return "未在公司知识库中检索到相关信息。"
            
        sources = data.get("sources", [])
        source_names = set([s.get("source") for s in sources if s.get("source")])
        
        res = f"【知识库内容】\n{answer}\n"
        if source_names:
            res += f"\n(来源文档: {', '.join(source_names)})"
        return res
        
    except requests.exceptions.ConnectionError:
        return "错误：无法连接内部 RAG 服务，请确认服务是否启动。"
    except Exception as e:
        return f"检索异常：{e}"

# ========== 2. 定义子 Agent ==========
# 检索 Agent：只负责找资料
retriever_agent = create_agent(
    model=llm,
    tools=[query_internal_rag],
    system_prompt="""你是一个资深的资料检索员。

当用户的问题包含多个独立的小问题时（例如“年假有几天？病假呢？”），你必须执行以下步骤：
1. 先提取第一个问题，调用工具 query_internal_rag 查询。
2. 把结果记录下来。
3. 再提取第二个问题，再次调用工具 query_internal_rag 查询。
4. 最后，把所有查到的资料合并在一起，原封不动地输出，不要总结。

如果只有一个问题，直接查一次即可。"""
)

# 撰写 Agent：只负责写报告，不调工具
writer_agent = create_agent(
    model=llm,
    tools=[],
    system_prompt="你是一个严谨的业务分析师。请仅根据用户提供的资料来回答问题。如果资料里没有，请直接说'未找到相关制度'，绝对不要自己编造。回答请条理清晰。"
)

# ========== 3. 定义状态与节点 ==========
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

def retrieve_node(state: AgentState):
    print("\n--- [检索员] 正在查询内部知识库 ---")
    result = retriever_agent.invoke({"messages": state["messages"]})
    
    # 只取出检索员的最终结果
    last_msg = result["messages"][-1]
    print(f"[检索员返回]: {last_msg.content[:100]}...")
    
    return {"messages": [last_msg]}

def write_node(state: AgentState):
    print("\n--- [业务分析师] 正在生成解答 ---")
    
    # ★ 关键：把用户的原始问题和检索到的资料提取出来，拼成干净的 Prompt
    original_question = state["messages"][0].content
    retrieved_data = state["messages"][-1].content
    
    clean_prompt = f"""用户的问题是：{original_question}
    
    检索员查到的资料如下：
    {retrieved_data}
    
    请根据上述资料回答用户问题。"""
    
    # 只把干净的 prompt 传给撰稿人
    result = writer_agent.invoke({"messages": [HumanMessage(content=clean_prompt)]})
    
    return {"messages": [result["messages"][-1]]}

# ========== 4. 组装图 ==========
workflow = StateGraph(AgentState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("write", write_node)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "write")
workflow.add_edge("write", END)

app = workflow.compile()

# ========== 5. 测试 ==========
if __name__ == "__main__":
    print("=== 企业内部知识库专家系统启动 ===")
    
    # 测试1：问一个知识库里有的事
    q1 = "帮我查一下公司年假有几天？另外，迟到会怎么扣钱？"
    print(f"\n用户提问: {q1}")
    result1 = app.invoke({"messages": [HumanMessage(content=q1)]})
    print("\n=== 最终回答 ===")
    print(result1["messages"][-1].content)

    # 测试2：问一个知识库里没有的事
    q2 = "公司食堂今天的菜谱是什么？"
    print(f"\n\n用户提问: {q2}")
    result2 = app.invoke({"messages": [HumanMessage(content=q2)]})
    print("\n=== 最终回答 ===")
    print(result2["messages"][-1].content)