"""Web research helper for ResearchPilot.

Provides live web search capabilities using DuckDuckGo search or custom search API wrappers.
Converts search results into standard LangChain Document objects for parallel evidence aggregation.
"""

from typing import Optional
from langchain_core.documents import Document


def search_web(query: str, max_results: int = 3) -> list[Document]:
    """Execute live web search and return standard Document objects.

    Args:
        query (str): The search query.
        max_results (int): Max search results to retrieve.

    Returns:
        list[Document]: List of retrieved web documents.
    """
    docs: list[Document] = []
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            for res in results:
                title = res.get("title", "")
                href = res.get("href", "")
                body = res.get("body", "")
                content = f"Title: {title}\nURL: {href}\nContent: {body}"
                doc = Document(
                    page_content=content,
                    metadata={"source": "web_search", "url": href, "title": title},
                )
                docs.append(doc)
    except Exception as e:
        # Fallback graceful error handling if network or search API is unavailable
        docs.append(
            Document(
                page_content=f"Web search for '{query}' unavailable: {str(e)}",
                metadata={"source": "web_search", "status": "error"},
            )
        )

    return docs
