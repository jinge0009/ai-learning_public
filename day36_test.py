import streamlit as st

st.title("我的第一个 AI 网页 🚀")
st.write("你好，这是我用 Streamlit 写的网页！")

# 侧边栏
with st.sidebar:
    st.header("设置")
    name = st.text_input("请输入你的名字：")

if name:
    st.success(f"你好，{name}！欢迎来到 AI 世界。")

# 按钮
if st.button("点我"):
    st.balloons()  # 放个气球动画