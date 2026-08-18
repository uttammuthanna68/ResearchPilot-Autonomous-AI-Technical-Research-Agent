"""Evaluation metrics module for ResearchPilot."""

import re
from typing import Any, Dict, List


def evaluate_response(case: Dict[str, Any], agent_output: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single agent response against an evaluation test case."""
    query = case["query"]
    expected_route = case["expected_route"]
    key_concepts = case.get("key_concepts", [])

    actual_route = agent_output.get("router", {}).get("type", "research")
    report = agent_output.get("report", "")
    documents = agent_output.get("documents", [])
    verification = agent_output.get("evidence_verification", {})

    # 1. Routing / Failure Handling Score
    route_correct = (actual_route == expected_route)
    safeguard_score = 1.0 if route_correct else 0.0

    # 2. Answer Relevance Score
    report_lower = report.lower()
    matched_concepts = [c for c in key_concepts if c.lower() in report_lower]
    relevance_score = len(matched_concepts) / len(key_concepts) if key_concepts else 1.0

    # 3. Citation / Source Availability Score
    has_citations = bool(re.search(r"\[\d+\]", report))
    has_sources = len(documents) > 0
    if expected_route != "research":
        citation_score = 1.0
    else:
        citation_score = (0.5 if has_citations else 0.0) + (0.5 if has_sources else 0.0)

    # 4. Evidence Grounding Score
    verification_status = verification.get("status", "supported")
    if expected_route != "research":
        grounding_score = 1.0
    elif verification_status in ("supported", "conflicting", "insufficient"):
        # Explicit grounding safeguards
        grounding_score = 1.0
    else:
        grounding_score = 0.5

    # 5. Retrieval Quality Score
    if expected_route != "research":
        retrieval_score = 1.0
    else:
        min_sources = case.get("min_sources", 1)
        retrieval_score = 1.0 if len(documents) >= min_sources else 0.5

    # 6. Autonomous Re-Planning Loop Metric
    loop_count = agent_output.get("research_loop_count", 0)
    if verification_status in ("insufficient", "conflicting"):
        replan_score = 1.0 if loop_count >= 1 else 0.8
    else:
        replan_score = 1.0

    # Weighted Overall Score
    overall_score = round(
        (0.25 * relevance_score)
        + (0.2 * grounding_score)
        + (0.2 * citation_score)
        + (0.1 * retrieval_score)
        + (0.15 * safeguard_score)
        + (0.1 * replan_score),
        2,
    )

    passed = (safeguard_score == 1.0) and (overall_score >= 0.70)

    return {
        "case_id": case["id"],
        "category": case["category"],
        "query": query,
        "expected_route": expected_route,
        "actual_route": actual_route,
        "passed": passed,
        "overall_score": overall_score,
        "metrics": {
            "relevance_score": round(relevance_score, 2),
            "grounding_score": round(grounding_score, 2),
            "citation_score": round(citation_score, 2),
            "retrieval_score": round(retrieval_score, 2),
            "safeguard_score": round(safeguard_score, 2),
            "replan_score": round(replan_score, 2),
        },
        "matched_concepts": matched_concepts,
        "source_count": len(documents),
        "verification_status": verification_status,
        "research_loop_count": loop_count,
    }

