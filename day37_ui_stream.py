import streamlit as st
import requests
import json

st.set_page_config(page_title="流式 AI 助手", page_icon="⚡")
st.title("⚡ 极速流式 AI 助手")

# 维护聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 渲染历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入问题
if prompt := st.chat_input("请输入您的问题..."):
    # 显示用户提问
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 显示 AI 的占位符
    with st.chat_message("assistant"):
        # ★ 核心：定义一个生成器，接收后端的流
        def get_stream():
            response = requests.post(
                "http://127.0.0.1:8001/chat_stream",
                json={"question": prompt},
                stream=True  # ★ 关键：requests 也要开启 stream
            )
            
            # 逐行读取
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        try:
                            data = json.loads(data_str)
                            if "text" in data:
                                yield data["text"]
                            elif "error" in data:
                                yield f"\n[错误: {data['error']}]"
                        except:
                            pass

        # 渲染打字机，并获取最终完整文本
        full_response = st.write_stream(get_stream())
        
        # 存入历史
        st.session_state.messages.append({"role": "assistant", "content": full_response})