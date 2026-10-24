# 使用官方 Python 轻量级基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖清单并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目所有代码到容器里
COPY . .

# 暴露 Streamlit 和 FastAPI 的默认端口
EXPOSE 8000
EXPOSE 8501

# 默认命令（会被 docker-compose 覆盖）
CMD ["uvicorn", "day37_rag_api:app", "--host", "0.0.0.0", "--port", "8000"]