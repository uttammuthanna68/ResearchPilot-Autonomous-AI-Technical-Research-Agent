"""Unit tests and mocks for the web search tool component."""

import asyncio
import json
from io import BytesIO
from unittest.mock import MagicMock, patch
import pytest
from langchain_core.documents import Document

from shared.tools.web_search import (
    search_web_provider,
    search_web_with_timeout,
    web_search_tool,
)


def test_duckduckgo_web_search_mock():
    """Test DuckDuckGo provider with mocked search results."""
    mock_ddgs = MagicMock()
    mock_ddgs.__enter__.return_value = mock_ddgs
    mock_ddgs.text.return_value = [
        {
            "title": "LangGraph Documentation",
            "href": "https://langchain.com/langgraph",
            "body": "LangGraph is a framework for stateful agent workflows.",
        }
    ]

    with patch("duckduckgo_search.DDGS", return_value=mock_ddgs):
        docs = search_web_provider("LangGraph", provider="duckduckgo", max_results=1)

    assert len(docs) == 1
    assert docs[0].metadata["source"] == "web_search"
    assert docs[0].metadata["provider"] == "duckduckgo"
    assert docs[0].metadata["url"] == "https://langchain.com/langgraph"
    assert docs[0].metadata["title"] == "LangGraph Documentation"
    assert "LangGraph is a framework" in docs[0].page_content


def test_tavily_web_search_mock():
    """Test Tavily HTTP API search with mocked response."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(
        {
            "results": [
                {
                    "title": "Tavily AI Docs",
                    "url": "https://tavily.com/doc",
                    "content": "Tavily search API snippet",
                }
            ]
        }
    ).encode("utf-8")
    mock_response.__enter__.return_value = mock_response

    with patch.dict("os.environ", {"TAVILY_API_KEY": "fake_tavily_key"}):
        with patch("urllib.request.urlopen", return_value=mock_response):
            docs = search_web_provider("AI Agents", provider="tavily", max_results=1)

    assert len(docs) == 1
    assert docs[0].metadata["provider"] == "tavily"
    assert docs[0].metadata["url"] == "https://tavily.com/doc"
    assert docs[0].metadata["title"] == "Tavily AI Docs"


@pytest.mark.asyncio
async def test_web_search_timeout_handling():
    """Test that search_web_with_timeout safely handles slow external APIs."""
    def slow_search(*args, **kwargs):
        import time
        time.sleep(1.0)
        return [Document(page_content="Slow result", metadata={"source": "web_search"})]

    with patch("shared.tools.web_search.search_web_provider", side_effect=slow_search):
        docs = await search_web_with_timeout("Test Query", timeout_seconds=0.1)

    assert docs == []  # Graceful fallback on timeout


@pytest.mark.asyncio
async def test_web_search_error_handling():
    """Test that search_web_with_timeout safely catches exceptions without crashing."""
    with patch("shared.tools.web_search.search_web_provider", side_effect=RuntimeError("Network offline")):
        docs = await search_web_with_timeout("Test Query", timeout_seconds=2.0)

    assert docs == []  # Graceful fallback on exception


def test_web_search_tool_formatting():
    """Test web_search_tool output string formatting."""
    mock_docs = [
        Document(
            page_content="Title: Test Article\nURL: https://example.com\nSnippet: Sample content",
            metadata={"title": "Test Article", "url": "https://example.com"},
        )
    ]
    with patch("shared.tools.web_search.search_web_provider", return_value=mock_docs):
        result = web_search_tool.invoke({"query": "Example"})

    assert "[1] Test Article" in result
    assert "https://example.com" in result
    assert "Sample content" in result
