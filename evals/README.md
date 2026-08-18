# ResearchPilot Evaluation Module

The evaluation module provides a reproducible, automated benchmarking suite for **ResearchPilot**.

It evaluates agent outputs across 10 technical test cases measuring answer relevance, evidence grounding, citation availability, retrieval quality, and safeguard intent routing.

---

## 1. Evaluation Dataset (`evals/dataset.json`)

The evaluation dataset contains 10 structured test cases across 8 technical domain categories:

1. **Architecture (`eval-001`)**: LangGraph State Persistence via Checkpointers.
2. **Algorithms (`eval-002`)**: HNSW vs IVF Vector Indexing Comparison.
3. **System Design (`eval-003`)**: Event-Driven Microservices vs RESTful Architecture.
4. **Databases (`eval-004`)**: ACID Relational Transactions vs NoSQL Eventual Consistency.
5. **API Design (`eval-005`)**: GraphQL vs REST API Trade-offs.
6. **Distributed Systems (`eval-006`)**: Raft Consensus Algorithm Leader Election.
7. **Cloud Infrastructure (`eval-007`)**: Kubernetes Pod Scheduling & Affinity Rules.
8. **Vague Safeguard (`eval-008`)**: Underspecified code error query (`more-info`).
9. **Off-Topic Safeguard (`eval-009`)**: Non-technical baking recipe query (`general`).
10. **Insufficient Context Safeguard (`eval-010`)**: Out-of-scope quantum computing query.

---

## 2. Evaluation Metrics (`evals/evaluator.py`)

Each case is scored against 5 quantitative metrics:

1. **Answer Relevance Score (0.0 - 1.0)**: Percentage of required domain key terms and concepts present in the synthesized report.
2. **Evidence Grounding Score (0.0 - 1.0)**: Assesses evidence verification status (`supported`, `conflicting`, `insufficient`) and absence of ungrounded claims.
3. **Citation / Source Availability Score (0.0 - 1.0)**: Verifies presence of numeric citations (`[1]`) and clickable source references.
4. **Retrieval Quality Score (0.0 - 1.0)**: Evaluates whether a sufficient count of relevant context documents was retrieved.
5. **Safeguard Routing Score (0.0 - 1.0)**: Validates correct intent classification (`research`, `more-info`, `general`).

**Pass Criterion**: A test case passes if `safeguard_score == 1.0` and `overall_score >= 0.70`.

---

## 3. How to Run the Evaluation Suite

Execute the CLI runner from the project root:

```powershell
.\.venv\Scripts\python.exe -m evals.run_eval
```

### Modes:
- **Live Gemini Mode**: Automatically activated when a valid `GEMINI_API_KEY` is present in `.env`.
- **Reproducible Offline Mode**: Automatically activated when offline or without API keys to provide deterministic baseline evaluation results.

The generated report will be saved to **`evals/results.md`**.
