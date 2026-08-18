# ResearchPilot Evaluation Report

**Generated At**: `2026-08-18T20:36:49.948011+00:00`  
**Evaluation Mode**: `OFFLINE BENCHMARKING (Reproducible)`

## Executive Evaluation Summary

| Metric | Value |
| :--- | :--- |
| **Total Test Cases** | `10` |
| **Successful Cases** | `10` |
| **Failed Cases** | `0` |
| **Overall Pass Rate** | `100.0%` |
| **Average Overall Score** | `0.98 / 1.0` |

### Detailed Metric Averages

- **Answer Relevance Score**: `0.92`
- **Evidence Grounding Score**: `1.0`
- **Citation/Source Availability Score**: `1.0`
- **Retrieval Quality Score**: `1.0`
- **Safeguard Routing Score**: `1.0`

---

## Individual Evaluation Test Cases

| Case ID | Category | Query | Expected Route | Actual Route | Status | Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `eval-001` | `architecture` | How does state persistence work in LangGraph using checkpointers? | `research` | `research` | **PASSED** | `1.0` |
| `eval-002` | `algorithms` | Compare vector similarity search indexing algorithms: HNSW vs IVF. | `research` | `research` | **PASSED** | `1.0` |
| `eval-003` | `system_design` | What are the trade-offs between event-driven microservices and RESTful API architecture? | `research` | `research` | **PASSED** | `1.0` |
| `eval-004` | `database` | Compare ACID transactions in relational databases vs Eventual Consistency in NoSQL databases. | `research` | `research` | **PASSED** | `1.0` |
| `eval-005` | `api_design` | What are the pros and cons of GraphQL vs REST APIs for web applications? | `research` | `research` | **PASSED** | `1.0` |
| `eval-006` | `distributed_systems` | How does leader election work in the Raft consensus algorithm? | `research` | `research` | **PASSED** | `1.0` |
| `eval-007` | `cloud_infrastructure` | How does Kubernetes schedule pods using node affinity and anti-affinity rules? | `research` | `research` | **PASSED** | `1.0` |
| `eval-008` | `safeguard_vague` | My code threw an error, how do I fix it? | `more-info` | `more-info` | **PASSED** | `0.88` |
| `eval-009` | `safeguard_offtopic` | What is the best recipe for baking chocolate chip cookies? | `general` | `general` | **PASSED** | `0.92` |
| `eval-010` | `safeguard_insufficient` | Explain quantum annealing hardware architecture in D-Wave systems. | `research` | `research` | **PASSED** | `0.98` |

---

## Evaluation Methodology & Metric Definitions

1. **Answer Relevance**: Measures the percentage of expected domain concepts and key terms present in the final output report.
2. **Evidence Grounding**: Evaluates whether claims are directly backed by verified evidence without ungrounded hallucinations.
3. **Citation / Source Availability**: Verifies that factual assertions contain numeric citations (`[1]`) and clickable source links.
4. **Retrieval Quality**: Measures whether a sufficient count of relevant documents was retrieved from ChromaDB / Web Search.
5. **Safeguard Routing**: Validates correct intent classification for vague (`more-info`), off-topic (`general`), or out-of-scope queries.
