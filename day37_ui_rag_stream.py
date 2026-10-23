import streamlit as st
import requests
import json

st.title("📚 企业知识库流式问答")

# 侧边栏添加文件上传
with st.sidebar:
    st.header("📄 知识库管理")
    uploaded_file = st.file_uploader("上传 PDF 或 TXT", type=["pdf", "txt"])
    if st.button("上传到知识库") and uploaded_file is not None:
        with st.spinner("正在解析并存入云端知识库..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            res = requests.post("http://124.220.164.171:8000/upload", files=files)
            if res.status_code == 200:
                st.success(f"上传成功！切分块数: {res.json().get('chunks')}")
            else:
                st.error(f"上传失败: {res.text}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # 如果这条消息带有来源信息，重新渲染折叠框
        if msg.get("sources"):
            with st.expander("📚 查看引用来源"):
                for s in msg["sources"]:
                    st.write(f"**{s.get('source')}** (相关度: {s.get('rerank_score')})")

if prompt := st.chat_input("请输入关于公司制度的问题..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        # ★ 使用一个列表来保存最新的 sources
        latest_sources = []

        def get_rag_stream():
            response = requests.post(
                "http://124.220.164.171:8000/chat_stream",
                json={"question": prompt},
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        try:
                            data = json.loads(data_str)
                            # 如果是文本，yield 给打字机
                            if "text" in data:
                                yield data["text"]
                            # 如果是来源，存起来，不展示在打字机里
                            elif data.get("type") == "sources":
                                latest_sources.extend(data["sources"])
                        except:
                            pass

        # 渲染打字机
        full_response = st.write_stream(get_rag_stream())
        
        # 打字机结束后，渲染来源
        if latest_sources:
            with st.expander("📚 查看引用来源"):
                for s in latest_sources:
                    st.write(f"**{s.get('source')}** (相关度: {s.get('rerank_score')})")

        # 将最终完整数据存入历史
        st.session_state.messages.append({
            "role": "assistant", 
            "content": full_response,
            "sources": latest_sources
        })