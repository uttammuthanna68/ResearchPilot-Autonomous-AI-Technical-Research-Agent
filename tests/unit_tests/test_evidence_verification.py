"""Unit tests for the Evidence Verification stage in ResearchPilot."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from retrieval_graph.graph import verify_evidence
from retrieval_graph.state import AgentState, EvidenceVerification


@pytest.mark.asyncio
async def test_verify_evidence_no_retrieved_evidence():
    """Test 1: No retrieved evidence returns status='insufficient' without crashing."""
    state = AgentState(
        messages=[HumanMessage(content="Explain quantum annealing")],
        documents=[],
    )
    config = RunnableConfig(configurable={})
    
    result = await verify_evidence(state, config=config)
    
    verification = result["evidence_verification"]
    assert verification["status"] == "insufficient"
    assert "No retrieved context" in verification["summary"]
    assert len(verification["missing_elements"]) > 0


@pytest.mark.asyncio
async def test_verify_evidence_supported_claim():
    """Test 2: Directly supporting evidence returns status='supported'."""
    doc = Document(
        page_content="LangGraph checkpointers persist graph state into SQLite or Postgres databases.",
        metadata={"title": "Checkpointer Guide", "url": "https://langchain.com/docs", "source": "knowledge_base"},
    )
    state = AgentState(
        messages=[HumanMessage(content="How does state persistence work in LangGraph?")],
        documents=[doc],
    )
    config = RunnableConfig(configurable={})

    mock_llm_response = {
        "status": "supported",
        "summary": "Retrieved document directly details checkpointer state persistence into SQLite/Postgres.",
        "verified_claims": ["Checkpointers save state to SQLite/Postgres"],
        "conflicting_claims": [],
        "missing_elements": [],
    }

    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(return_value=mock_llm_response)

    with patch("retrieval_graph.graph.load_chat_model") as mock_load_model:
        mock_load_model.return_value.with_structured_output.return_value = mock_model
        result = await verify_evidence(state, config=config)

    verification = result["evidence_verification"]
    assert verification["status"] == "supported"
    assert len(verification["verified_claims"]) > 0
    assert verification["conflicting_claims"] == []


@pytest.mark.asyncio
async def test_verify_evidence_unsupported_claim():
    """Test 3: Unrelated or insufficient evidence returns status='insufficient'."""
    doc = Document(
        page_content="Python is a dynamic programming language created by Guido van Rossum.",
        metadata={"title": "Python Intro", "url": "https://python.org", "source": "web_search"},
    )
    state = AgentState(
        messages=[HumanMessage(content="Explain D-Wave quantum annealing hardware architecture")],
        documents=[doc],
    )
    config = RunnableConfig(configurable={})

    mock_llm_response = {
        "status": "insufficient",
        "summary": "Retrieved document discusses Python history, which does not answer quantum hardware.",
        "verified_claims": [],
        "conflicting_claims": [],
        "missing_elements": ["D-Wave hardware architecture", "Quantum annealing details"],
    }

    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(return_value=mock_llm_response)

    with patch("retrieval_graph.graph.load_chat_model") as mock_load_model:
        mock_load_model.return_value.with_structured_output.return_value = mock_model
        result = await verify_evidence(state, config=config)

    verification = result["evidence_verification"]
    assert verification["status"] == "insufficient"
    assert len(verification["missing_elements"]) > 0


@pytest.mark.asyncio
async def test_verify_evidence_conflicting_sources():
    """Test 4: Contradictory sources return status='conflicting'."""
    doc1 = Document(
        page_content="HNSW indexing requires O(N log N) memory overhead during construction.",
        metadata={"title": "HNSW Paper 2020", "url": "https://example.com/a", "source": "knowledge_base"},
    )
    doc2 = Document(
        page_content="HNSW indexing has flat O(1) memory overhead regardless of vector count.",
        metadata={"title": "Vector DB Blog", "url": "https://example.com/b", "source": "web_search"},
    )
    state = AgentState(
        messages=[HumanMessage(content="What is the memory complexity of HNSW indexing?")],
        documents=[doc1, doc2],
    )
    config = RunnableConfig(configurable={})

    mock_llm_response = {
        "status": "conflicting",
        "summary": "Source 1 states O(N log N) memory, while Source 2 claims flat O(1) memory.",
        "verified_claims": ["HNSW uses graph structure"],
        "conflicting_claims": ["Source 1 claims O(N log N) memory complexity, Source 2 claims O(1)"],
        "missing_elements": [],
    }

    mock_model = MagicMock()
    mock_model.ainvoke = AsyncMock(return_value=mock_llm_response)

    with patch("retrieval_graph.graph.load_chat_model") as mock_load_model:
        mock_load_model.return_value.with_structured_output.return_value = mock_model
        result = await verify_evidence(state, config=config)

    verification = result["evidence_verification"]
    assert verification["status"] == "conflicting"
    assert len(verification["conflicting_claims"]) > 0
