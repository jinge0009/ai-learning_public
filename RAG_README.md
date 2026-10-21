# RAG 知识库问答系统

基于 FastAPI + Chroma + 大模型的检索增强生成系统。

## 功能

- 支持 PDF / Word / TXT / Markdown 文档上传
- 自动切分、向量化、存入向量数据库
- 两阶段检索：向量粗排 + Rerank 精排
- 基于检索结果生成回答，标注来源
- 支持批量上传、问答历史

## 技术栈

- **Web 框架**：FastAPI
- **向量数据库**：Chroma
- **Embedding**：腾讯云 kinfra-text-embedding
- **Rerank**：BAAI/bge-reranker-base
- **大模型**：DeepSeek-Flash

## 架构

```text
用户提问
    ↓
向量检索 Top 20（粗排）
    ↓
Rerank 精排 Top 3
    ↓
拼接 Prompt
    ↓
大模型生成回答
    ↓
返回答案 + 来源
```

## API

| 接口 | 方法 | 功能 |
|------|------|------|
| `/upload` | POST | 上传单个文档 |
| `/upload-batch` | POST | 批量上传 |
| `/chat` | POST | 提问 |
| `/history` | GET | 问答历史 |
| `/documents` | GET | 文档列表 |
| `/documents/{name}` | DELETE | 删除文档 |

## 运行

```bash
pip install -r requirements.txt
uvicorn day28_rag_api:app --reload
```

访问 `http://127.0.0.1:8000/docs`。

## 关键设计

- **切分策略**：chunk_size=200，overlap=30，尽量在句子边界切
- **余弦距离**：向量检索用余弦，比欧氏更适合文本
- **两阶段检索**：粗排保证不漏，精排保证准确
- **Prompt 约束**：只根据资料回答，防止幻觉

