import streamlit as st
from langchain_core.messages import HumanMessage

# 导入你 Day 32 代码里创建的 agent 和 load_profile
# 注意：确保 day32_final_agent.py 里的代码是可以被 import 的（没有死循环阻塞）
from day32_final_agent import agent, load_profile 

st.title("🧠 全能私人助理 (Web版)")

if "messages" not in st.session_state:
    st.session_state.messages = []
    
# 侧边栏展示长期记忆
with st.sidebar:
    st.header("📂 用户档案")
    profile = load_profile()
    if profile.get("facts"):
        for fact in profile["facts"]:
            st.write(f"- {fact}")
    else:
        st.write("暂无记忆")
    
    if st.button("清空对话"):
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("有什么我可以帮你的吗？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            # 调用本地 Agent
            # 注意：这里为了演示，只传当前的 prompt。正式项目需传入历史列表
            result = agent.invoke({"messages": [("user", prompt)]})
            answer = result["messages"][-1].content
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})