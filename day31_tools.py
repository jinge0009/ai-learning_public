import os
import requests
from langchain_core.tools import tool

@tool
def search_wikipedia(query: str) -> str:
    """在维基百科上搜索词条摘要。当你需要查询人物、地点、历史事件等背景知识时使用。"""
    try:
        # 维基百科公开 API
        url = "https://zh.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": 1,
            "srlimit": 1
        }
        # 加上 User-Agent，防止被维基百科拦截
        headers = {"User-Agent": "MyAgent/1.0 (test@example.com)"}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("query", {}).get("search", [])
        if not results:
            return f"维基百科上没有找到关于【{query}】的词条。"
        
        # 获取第一条结果的摘要（需要再请求一次）
        page_title = results[0]["title"]
        snippet = results[0]["snippet"].replace('<span class="searchmatch">', '').replace('</span>', '')
        
        return f"找到维基百科词条【{page_title}】：{snippet}..."
    except Exception as e:
        return f"搜索失败：{e}"

@tool
def query_internal_knowledge(question: str) -> str:
    """查询企业内部的 RAG 知识库。当你需要回答关于公司制度、产品文档、内部规定等问题时使用。"""
    try:
        # 请求你本地的 FastAPI 服务
        response = requests.post(
            "http://127.0.0.1:8000/chat",
            json={"question": question},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        answer = data.get("answer", "未获取到答案")
        sources = data.get("sources", [])
        
        # 如果大模型明确说不知道，我们把这句话返回给 Agent
        if "无法回答" in answer:
            return "内部知识库中没有找到相关信息。"
            
        source_text = ""
        if sources:
            source_text = f"\n(来源: {sources[0].get('source')})"
            
        return f"{answer}{source_text}"
        
    except requests.exceptions.ConnectionError:
        return "连接内部知识库失败，请确认 RAG 服务是否已启动。"
    except Exception as e:
        return f"查询知识库时出错：{e}"