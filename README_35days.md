# AI 应用独立开发实战（35天）

这是一个从零基础到独立开发 AI 应用的实战记录。涵盖了 RAG、Agent 编排、多 Agent 协作等核心技术，所有代码均可运行。

## 🚀 核心项目展示

### 1. 企业级 RAG 知识库问答系统 (`day28_rag_api.py`)
- **技术栈**：FastAPI + Chroma + BGE-Rerank + DeepSeek
- **亮点**：支持 PDF 上传切分；采用**两阶段检索**（向量粗排 + Rerank 精排），有效提升召回率；配备阈值过滤，从物理层防止模型幻觉。
- **功能**：文档管理、流式问答、来源溯源。

### 2. 多 Agent 协作内容生成团队 (`day33_multi_agent.py`)
- **技术栈**：LangGraph + LangChain
- **亮点**：实现 Supervisor-Workers 架构。包含“研究员、撰稿人、审核员、翻译员”四个独立 Agent。通过状态图（StateGraph）传递消息，审核员能自主发现逻辑矛盾并打回重写。

### 3. 企业内部知识库专家 (`day34_rag_agent.py`)
- **技术栈**：LangGraph + Agent + 本地 RAG API
- **亮点**：将 RAG 封装为 Agent 的工具。实现“检索员（查资料）+ 分析师（写报告）”的职责分离。面对知识库没有的问题，能诚实拒绝，彻底解决大模型胡编乱造的问题。

## 🛠️ 环境运行
```bash
pip install -r requirements.txt
uvicorn day28_rag_api:app --reload