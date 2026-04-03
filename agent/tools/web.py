import os
from duckduckgo_search import DDGS
from langchain_core.tools import tool

@tool
def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for information.
    Use this when you need up-to-date facts, documentation, or external knowledge not in your training data.

    Args:
        query: The search query string.
        max_results: Number of results to return (default 5).
    """
    print(f"\033[35m[联网搜索]\033[0m 正在检索: {query}")

    proxy = os.getenv("HIS_PROXY", default=None)

    try:
        with DDGS(proxy=proxy, timeout=20) as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return "No results found for your query."

        output = []
        for i, res in enumerate(results):
            title = res.get('title', 'No Title')
            href = res.get('href', 'No URL')
            body = res.get('body', 'No Description')
            output.append(f"{i + 1}. TITLE: {title}\n   URL: {href}\n   SUMMARY: {body}\n")

        return "\n".join(output)

    except Exception as e:
        error_msg = str(e)
        print(f"\033[31m[网络拦截] 搜索失败: {error_msg}\033[0m")
        return (
            f"Network Error: Unable to reach the search engine due to domestic network restrictions or timeout. "
            f"Detailed error: {error_msg}. "
            f"CRITICAL INSTRUCTION: DO NOT retry the exact same search. Either try a different approach, "
            f"or proceed using your existing internal knowledge."
        )