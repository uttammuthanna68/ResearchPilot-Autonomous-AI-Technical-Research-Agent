"""Web Search Tool Component for ResearchPilot.

Provides a robust, configurable web search tool supporting multiple search providers
(DuckDuckGo as zero-config default, Tavily, Serper) with strict timeout controls
and error handling safeguards to guarantee zero-downtime RAG operations.
"""

import json
import os
import asyncio
import urllib.request
from typing import Literal, Optional
from langchain_core.documents import Document
from langchain_core.tools import tool


def search_web_provider(
    query: str,
    provider: str = "duckduckgo",
    max_results: int = 3,
) -> list[Document]:
    """Execute web search using the specified provider.

    Args:
        query (str): The search query string.
        provider (str): Provider choice ('duckduckgo', 'tavily', 'serper').
        max_results (int): Maximum number of search results to return.

    Returns:
        list[Document]: Structured list of Document objects with URL and title metadata.
    """
    docs: list[Document] = []

    if provider == "tavily":
        tavily_key = os.environ.get("TAVILY_API_KEY")
        if tavily_key:
            try:
                payload = json.dumps(
                    {"api_key": tavily_key, "query": query, "max_results": max_results}
                ).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.tavily.com/search",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    for res in res_data.get("results", []):
                        title = res.get("title", "")
                        url = res.get("url", "")
                        content = res.get("content", "")
                        docs.append(
                            Document(
                                page_content=f"Title: {title}\nURL: {url}\nSnippet: {content}",
                                metadata={
                                    "source": "web_search",
                                    "provider": "tavily",
                                    "url": url,
                                    "title": title,
                                },
                            )
                        )
                return docs
            except Exception as e:
                print(f"[WebSearch Warning] Tavily API failed: {e}. Falling back to DuckDuckGo.")

    elif provider == "serper":
        serper_key = os.environ.get("SERPER_API_KEY")
        if serper_key:
            try:
                payload = json.dumps({"q": query, "num": max_results}).encode("utf-8")
                req = urllib.request.Request(
                    "https://google.serper.dev/search",
                    data=payload,
                    headers={
                        "X-API-KEY": serper_key,
                        "Content-Type": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    for res in res_data.get("organic", []):
                        title = res.get("title", "")
                        url = res.get("link", "")
                        snippet = res.get("snippet", "")
                        docs.append(
                            Document(
                                page_content=f"Title: {title}\nURL: {url}\nSnippet: {snippet}",
                                metadata={
                                    "source": "web_search",
                                    "provider": "serper",
                                    "url": url,
                                    "title": title,
                                },
                            )
                        )
                return docs
            except Exception as e:
                print(f"[WebSearch Warning] Serper API failed: {e}. Falling back to DuckDuckGo.")

    # Default Zero-Config Provider: DuckDuckGo
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            for res in results:
                title = res.get("title", "")
                href = res.get("href", "")
                body = res.get("body", "")
                content = f"Title: {title}\nURL: {href}\nSnippet: {body}"
                docs.append(
                    Document(
                        page_content=content,
                        metadata={
                            "source": "web_search",
                            "provider": "duckduckgo",
                            "url": href,
                            "title": title,
                        },
                    )
                )
    except Exception as e:
        print(f"[WebSearch Error] DuckDuckGo search failed: {e}")

    return docs


async def search_web_with_timeout(
    query: str,
    provider: str = "duckduckgo",
    max_results: int = 3,
    timeout_seconds: float = 8.0,
) -> list[Document]:
    """Execute web search with asynchronous timeout and error handling.

    Args:
        query (str): Search query.
        provider (str): Web search provider.
        max_results (int): Max search results.
        timeout_seconds (float): Timeout limit in seconds.

    Returns:
        list[Document]: Retrieved documents or empty list on timeout/error.
    """
    try:
        loop = asyncio.get_running_loop()
        docs = await asyncio.wait_for(
            loop.run_in_executor(
                None, search_web_provider, query, provider, max_results
            ),
            timeout=timeout_seconds,
        )
        return docs
    except asyncio.TimeoutError:
        print(f"[WebSearch Warning] Web search timed out after {timeout_seconds}s for query: '{query}'")
        return []
    except Exception as e:
        print(f"[WebSearch Warning] Web search encountered error: {e}")
        return []


@tool
def web_search_tool(query: str) -> str:
    """Tool to perform a web search for current technical documentation and real-time info.

    Args:
        query (str): The technical search query.

    Returns:
        str: Formatted string of search results with titles and URLs.
    """
    docs = search_web_provider(query, provider="duckduckgo", max_results=3)
    if not docs:
        return f"No web search results found for query: '{query}'."

    formatted = []
    for i, doc in enumerate(docs, 1):
        url = doc.metadata.get("url", "N/A")
        title = doc.metadata.get("title", "Untitled")
        formatted.append(f"[{i}] {title}\nURL: {url}\n{doc.page_content}\n")
    return "\n---\n".join(formatted)
