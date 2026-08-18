"""Unit tests for the ResearchPilot Evaluation Module."""

import pytest
from evals.evaluator import evaluate_response


def test_evaluate_response_supported_case():
    """Test evaluation calculation for a well-supported technical query."""
    case = {
        "id": "eval-test-1",
        "category": "architecture",
        "expected_route": "research",
        "query": "How does state persistence work in LangGraph using checkpointers?",
        "key_concepts": ["checkpointer", "state", "persist"],
        "min_sources": 1,
    }

    agent_output = {
        "router": {"type": "research"},
        "steps": ["Investigate checkpointers"],
        "evidence_verification": {"status": "supported", "summary": "Verified"},
        "documents": [{"title": "Doc 1", "url": "https://example.com", "source": "knowledge_base"}],
        "report": "# Technical Research Report\n\nLangGraph uses a checkpointer to persist state [1].",
    }

    result = evaluate_response(case, agent_output)

    assert result["case_id"] == "eval-test-1"
    assert result["passed"] is True
    assert result["actual_route"] == "research"
    assert result["metrics"]["relevance_score"] == 1.0
    assert result["metrics"]["safeguard_score"] == 1.0
    assert result["overall_score"] >= 0.70


def test_evaluate_response_safeguard_case():
    """Test evaluation calculation for vague query routing safeguard."""
    case = {
        "id": "eval-test-2",
        "category": "safeguard_vague",
        "expected_route": "more-info",
        "query": "My code threw an error, how do I fix it?",
        "key_concepts": ["error", "code"],
        "min_sources": 0,
    }

    agent_output = {
        "router": {"type": "more-info"},
        "steps": [],
        "evidence_verification": {},
        "documents": [],
        "report": "Could you please provide the error message and code snippet?",
    }

    result = evaluate_response(case, agent_output)

    assert result["passed"] is True
    assert result["actual_route"] == "more-info"
    assert result["metrics"]["safeguard_score"] == 1.0


def test_evaluate_response_routing_mismatch():
    """Test evaluation calculation when routing fails expected classification."""
    case = {
        "id": "eval-test-3",
        "category": "safeguard_offtopic",
        "expected_route": "general",
        "query": "What is the best chocolate cake recipe?",
        "key_concepts": [],
        "min_sources": 0,
    }

    # Wrong routing (routed to research instead of general)
    agent_output = {
        "router": {"type": "research"},
        "steps": ["Bake cake"],
        "evidence_verification": {},
        "documents": [],
        "report": "Cake recipe...",
    }

    result = evaluate_response(case, agent_output)

    assert result["passed"] is False
    assert result["metrics"]["safeguard_score"] == 0.0
