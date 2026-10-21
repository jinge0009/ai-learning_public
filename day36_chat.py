import streamlit as st
import requests

# 设置页面配置
st.set_page_config(page_title="企业知识库助手", page_icon="🤖")
st.title("🤖 企业知识库智能助手")

# 初始化聊天历史（存在 Streamlit 的 session_state 中）
if "messages" not in st.session_state:
    st.session_state.messages = []

# 展示历史对话
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 聊天输入框（固定在页面底部）
if prompt := st.chat_input("请输入您的问题..."):
    # 1. 显示用户的提问
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. 调用后端 RAG API
    with st.chat_message("assistant"):
        with st.spinner("AI 正在查阅文档..."):
            try:
                # 发送 POST 请求
                response = requests.post(
                    "http://127.0.0.1:8000/chat",
                    json={"question": prompt, "fine_k": 3},
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                answer = data.get("answer", "未获取到回答")
                sources = data.get("sources", [])
                
                # 展示回答
                st.markdown(answer)
                
                # 展示来源文档
                if sources:
                    with st.expander("📚 查看引用来源"):
                        for i, s in enumerate(sources, 1):
                            st.write(f"**{i}. {s.get('source')}** (相关度: {s.get('rerank_score')})")
                            st.caption(f"原文片段: {s.get('preview')}...")

                # 存入历史
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                st.error(f"请求失败，请检查后端服务是否启动：{e}")