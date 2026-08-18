import os
import tempfile
import pytest
from langchain_core.runnables import RunnableConfig

from index_graph import graph as index_graph
from retrieval_graph import graph
from shared.configuration import BaseConfiguration


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") == "your_gemini_api_key_here",
    reason="Integration test requires a valid GEMINI_API_KEY",
)
async def test_retrieval_graph() -> None:
    simple_doc = 'In LangGraph, nodes are typically python functions (sync or async) where the first positional argument is the state, and (optionally), the second positional argument is a "config", containing optional configurable parameters (such as a thread_id).'
    
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        config = RunnableConfig(
            configurable={
                "retriever_provider": "chroma",
                "embedding_model": "google_genai/models/text-embedding-004",
                "chroma_persist_directory": tmp_dir,
            }
        )

        doc_id = "test_id"
        result = await index_graph.ainvoke(
            {"docs": [{"page_content": simple_doc, "id": doc_id}]}, config
        )
        assert result["docs"] == [] or result["docs"] == "delete"

        # test general query
        res = await graph.ainvoke(
            {"messages": [("user", "Hi! How are you?")]},
            config,
        )
        assert "general" in res["router"]["type"]

        # test query that needs more info
        res = await graph.ainvoke(
            {"messages": [("user", "I am having issues with the tools")]},
            config,
        )
        assert "more-info" in res["router"]["type"]

        # test LangChain-related query
        res = await graph.ainvoke(
            {"messages": [("user", "What is a node in LangGraph?")]},
            config,
        )
        assert "langchain" in res["router"]["type"]
        response = str(res["messages"][-1].content)
        assert len(response) > 0
