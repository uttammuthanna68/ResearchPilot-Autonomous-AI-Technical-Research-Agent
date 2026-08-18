[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-Vercel-brightgreen.svg?style=for-the-badge)](https://research-pilot-autonomous-ai-techni.vercel.app/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Google Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-green.svg)](https://ai.google.dev/)
[![Next.js 16](https://img.shields.io/badge/Frontend-Next.js%2016-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> 🌐 **Live Web Application**: [https://research-pilot-autonomous-ai-techni.vercel.app/](https://research-pilot-autonomous-ai-techni.vercel.app/)

**ResearchPilot** is an autonomous, multi-agent AI technical research assistant built with **LangGraph**, **Google Gemini**, **ChromaDB**, **FastAPI**, and **Next.js**. It performs deep, multi-step technical research across software engineering, AI/ML, cloud architecture, system design, and database topics.


Unlike simple Q&A chatbots, ResearchPilot executes a structured research pipeline: analyzing technical intent, generating multi-step research plans, retrieving evidence in parallel from both a local vector database and live web search, verifying claim support to prevent hallucinations, and synthesizing cited technical reports.

---

## 📸 Dashboard Preview & Demo

```
 ┌───────────────────────────────────────────────────────────────────────────────────────────┐
 │  RP  ResearchPilot — Autonomous AI Technical Research Agent      [Backend: Online]        │
 ├───────────────────────────────────────────────────────────────────────────────────────────┤
 │  Technical Research Console                                                               │
 │  [ How does state persistence work in LangGraph using checkpointers?                  ]   │
 │  Mode: (•) Hybrid (Dual)  ( ) Knowledge Base  ( ) Web Research   [Start Autonomous Research] │
 ├───────────────────────────────────────────────────────────────────────────────────────────┤
 │  Autonomous Agent Workflow Execution Pipeline                                             │
 │  [Query Analysis: ✓] ➔ [Planning: ✓] ➔ [Tasks: ✓] ➔ [Retrieval: ✓] ➔ [Verify: ✓] ➔ [Report: ✓]│
 ├───────────────────────────────────────────────────────────────────────────────────────────┤
 │  # Technical Research Report: LangGraph State Persistence via Checkpointers             │
 │                                                                                           │
 │  ## 1. Research Question                                                                  │
 │  How does state persistence work in LangGraph using checkpointers?                        │
 │                                                                                           │
 │  ## 2. Executive Summary                                                                  │
 │  LangGraph implements state persistence by checkpointing the graph state after step... [1]│
 │                                                                                           │
 │  ## 5. Evidence & Source References                                                       │
 │  - [1] LangGraph Persistence Conceptual Guide - (Source: Knowledge Base)                 │
 └───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

- 🧠 **Autonomous Research Planning & Re-Planning**: Decomposes complex inquiries into structured research plans and **autonomously loops back** to generate targeted follow-up queries if evidence verification detects context gaps or conflicting claims.
- ⚡ **Dual Retrieval Engine**: Simultaneously searches an in-process local **ChromaDB** vector store and live **Web Search APIs** using LangGraph `Send` primitives for parallel execution.
- 📁 **Multi-Format Document Ingestion**: Ingests and chunks **PDFs**, **Markdown**, **Plain Text**, and **JSON** files into ChromaDB vector store via FastAPI file upload modal.
- 🛡️ **Evidence Verification Engine**: Includes an explicit `verify_evidence` graph node that evaluates claim support (`supported`, `insufficient`, `conflicting`) to enforce strict grounding safeguards and eliminate hallucinations.
- 📄 **Structured 8-Section Reports**: Formats technical reports with Executive Summary, Key Findings, Detailed Analysis (separating evidence from interpretation), Source References, Conflicting Details, Limitations, and Conclusion.
- 🔗 **Clickable Numeric Citations**: Maps every factual assertion to numeric in-text citations (`[1]`, `[2]`) linked directly to verified URLs and document metadata.
- 📊 **Real-Time Next.js Dashboard**: Server-Sent Events (SSE) stream live graph execution progress (stage status, active task list, re-planning loop counters, retrieved source counter) to a dark-themed UI.
- 💾 **Persistent Session History**: Embedded **SQLite** database (`./data/history.db`) stores completed research reports, allowing users to reopen or delete historical investigations.
- 📈 **Automated Evaluation Suite**: 10-case evaluation module (`evals/`) measuring answer relevance, evidence grounding, citation availability, retrieval quality, re-planning loop efficiency, and safeguard intent routing.

---

## 📐 System Architecture

```
                               ┌───────────────────────────┐
                               │       User Inquiry        │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │  Analyze & Route Query    │
                               └──────┬──────┬──────┬──────┘
                                      │      │      │
            ┌─────────────────────────┘      │      └─────────────────────────┐
            ▼                                ▼                                ▼
   ┌─────────────────┐             ┌───────────────────┐             ┌─────────────────┐
   │ Ask for Details │             │ Technical Research│             │ Non-Technical   │
   │  (`more-info`)  │             │    (`research`)   │             │   (`general`)   │
   └─────────────────┘             └─────────┬─────────┘             └─────────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │   Create Research Plan    │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │ Execute Researcher Subgraph│◄─────────────────┐
                               │  (Send Parallel Tasks)    │                  │
                               └──────┬─────────────┬──────┘                  │
                                      │             │                         │ Re-planning Loop
                       ┌──────────────┘             └──────────────┐          │ (if insufficient /
                       ▼                                           ▼          │  conflicting &
          ┌─────────────────────────┐                 ┌─────────────────────────┐ │  loop_count < max)
          │  Local ChromaDB Vector  │                 │  Web Search Engine API  │ │
          │  (PDF / Text / Markdown)│                 │     (`web_search`)      │ │
          └────────────┬────────────┘                 └────────────┬────────────┘ │
                       │                                           │              │
                       └────────────────────┬──────────────────────┘              │
                                            ▼                                     │
                               ┌───────────────────────────┐                      │
                               │      Evidence Layer       │                      │
                               │  (Deduplicate via MD5)    │                      │
                               └────────────┬──────────────┘                      │
                                            ▼                                     │
                               ┌───────────────────────────┐                      │
                               │   Evidence Verification   │──────────────────────┘
                               │   (`verify_evidence`)     │
                               └────────────┬──────────────┘
                                            │ (supported OR max loops reached)
                                            ▼
                               ┌───────────────────────────┐
                               │ Structured Report Synthesizer
                               │  (8-Section Cited Report) │
                               └───────────────────────────┘
```


---

## 🛠️ Technology Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Agent Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) / [LangChain](https://github.com/langchain-ai/langchain) | StateGraph execution loops, state reducers, subgraphs, parallel `Send` tasks. |
| **LLM Provider** | [Google Gemini](https://ai.google.dev/) | `gemini-1.5-flash` for reasoning/synthesis; `models/text-embedding-004` for dense vector embeddings. |
| **Vector Store** | [ChromaDB](https://www.trychroma.com/) | In-process embedded vector database persisted locally to `./data/chroma`. |
| **Web Research** | [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search/) / Tavily / Serper | Zero-config web search with 8.0s timeout limit and fallback protection. |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn | Asynchronous REST and Server-Sent Events (SSE) streaming server (`http://127.0.0.1:8000`). |
| **History Database** | [SQLite](https://www.sqlite.org/) | Embedded database (`./data/history.db`) for persistent research session management. |
| **Frontend Dashboard**| [Next.js 16](https://nextjs.org/) + TypeScript + Tailwind CSS | Production web console featuring real-time workflow tracking (`http://localhost:3000`). |

---

## 🚀 Quick Start & Local Setup

### Prerequisites
- **Python**: `3.11` or `3.12`
- **Node.js**: `18.0` or higher (with `npm`)
- **Google Gemini API Key**: Obtain a key from [Google AI Studio](https://aistudio.google.com/).

### 1. Clone & Set Up Python Environment

```powershell
# Clone the repository
git clone https://github.com/your-username/ResearchPilot.git
cd ResearchPilot

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate      # Windows
# source .venv/bin/activate   # Linux/macOS

# Install backend dependencies
pip install -e .
pip install fastapi uvicorn duckduckgo-search
```

### 2. Configure Environment Variables

Create a `.env` file in the project root based on `.env.example`:

```ini
# Required: Google Gemini API Key
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Default zero-config settings
ENABLE_WEB_SEARCH=true
```

### 3. Set Up Frontend Dashboard

```powershell
cd frontend
npm install
cd ..
```

---

## 💻 Running ResearchPilot

### Option A: Launch Web Dashboard (Recommended)

Start both backend API and frontend dev servers in separate terminals:

```powershell
# Terminal 1: Start FastAPI Backend Server
.\.venv\Scripts\python.exe src/server.py

# Terminal 2: Start Next.js Frontend Dashboard
cd frontend
npm run dev
```

Open **`http://localhost:3000`** in your browser to access the ResearchPilot Dashboard.

### Option B: Run Python Verification Suite

To verify system performance across 5 distinct research scenarios directly via CLI:

```powershell
.\.venv\Scripts\python.exe scripts/test_five_queries.py
```

---

## 📊 Evaluation & Benchmarking

ResearchPilot includes an automated evaluation module (`evals/`) containing 10 technical test cases that evaluate answer relevance, evidence grounding, citation availability, retrieval quality, and safeguard intent routing.

To execute the evaluation suite and generate `evals/results.md`:

```powershell
.\.venv\Scripts\python.exe -m evals.run_eval
```

> **Evaluation Metric Scores**: Grounding: `1.0` | Citation Availability: `1.0` | Safeguard Routing: `1.0` | Pass Rate: `100%`

---

## ☁️ Cloud Deployment Architecture

ResearchPilot is designed for decoupled, zero-cost cloud deployment:

```
                   ┌───────────────┐
                   │    Vercel     │
                   │   Frontend    │
                   └───────┬───────┘
                           │ (SSE / REST API)
                           ▼
                   ┌───────────────┐
                   │  FastAPI &    │
                   │  LangGraph    │
                   └───────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         Google Gemini  ChromaDB   DuckDuckGo /
           (LLM API)   (Vector DB) Web Search API
```

### 1. Deploy Frontend to Vercel

1. Import your GitHub repository into [Vercel](https://vercel.com).
2. Set the **Root Directory** to `frontend`.
3. Select **Next.js** as the Framework Preset.
4. Add the Environment Variable:
   - `NEXT_PUBLIC_BACKEND_URL`: `https://your-backend-service.onrender.com`
5. Click **Deploy**.

### 2. Deploy Backend API (Render / Railway / Cloud Run)

1. Create a Web Service on [Render](https://render.com), [Railway](https://railway.app), or Google Cloud Run pointing to your repository root.
2. Set **Build Command**:
   ```bash
   pip install -e . && pip install fastapi uvicorn duckduckgo-search
   ```
3. Set **Start Command**:
   ```bash
   python src/server.py
   ```
4. Configure Environment Variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `ENABLE_WEB_SEARCH`: `true`
5. Click **Deploy**.

---

## 🔄 Significant Modifications from Original Template

This project was developed by extending and transforming the open-source [LangGraph RAG Research Agent Template](https://github.com/langchain-ai/rag-research-agent-template). Key architectural modifications include:

1. **LLM & Embedding Provider Migration**: Converted from OpenAI/Anthropic to **Google Gemini** (`gemini-1.5-flash`, `models/text-embedding-004`).
2. **Vector Store Simplification**: Replaced heavy external Elasticsearch cluster requirements with an embedded, zero-config local **ChromaDB** instance (`./data/chroma`).
3. **Domain Generalization**: Expanded the scope from LangChain-specific queries to general-purpose software engineering, AI/ML, cloud architecture, system design, and database topics.
4. **Dual Retrieval & Web Search Tool**: Added a multi-provider web search tool (`duckduckgo`, `tavily`, `serper`) with an 8.0-second async timeout guard.
5. **Evidence Verification Node**: Added an explicit `verify_evidence` graph node to evaluate context support and prevent ungrounded hallucinations.
6. **Structured 8-Section Markdown Reports**: Upgraded output formatting to generate cited engineering research reports.
7. **Production Next.js Web Console**: Created a Next.js App Router frontend consuming Server-Sent Events for live workflow execution tracking.
8. **Persistent Session Storage**: Added a lightweight SQLite storage layer (`src/shared/history_db.py`) for managing session history.
9. **Automated Evaluation Module**: Built an evaluation suite (`evals/`) to benchmark system quality.

---

## 📜 Attributions & Credits

- **LangGraph & LangChain**: Special thanks to Harrison Chase and the [LangChain AI team](https://github.com/langchain-ai) for creating the underlying **LangGraph** multi-agent orchestration framework.
- **Starting Template**: Initial graph structure adapted from the [LangGraph RAG Research Agent Template](https://github.com/langchain-ai/rag-research-agent-template).
- **Google Gemini**: Powered by Google DeepMind's [Gemini API](https://ai.google.dev/).
- **Open-Source Ecosystem**: Built using [ChromaDB](https://www.trychroma.com/), [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search/), [FastAPI](https://fastapi.tiangolo.com/), and [Next.js](https://nextjs.org/).

---

## ⚠️ Limitations & Future Roadmap

- **Document Indexing Format**: Currently optimized for Markdown and plaintext documentation. PDF and multi-modal document parsing will be added in future releases.
- **Rate Limits**: Web search tool uses zero-config DuckDuckGo by default; high-frequency automated batch queries should configure a paid `TAVILY_API_KEY`.
- **Future Roadmap**:
  - Add PDF file upload directly in the frontend UI.
  - Implement streaming token-by-token report synthesis.
  - Support user-customizable research plan depth (e.g. Deep Research mode with 5+ steps).

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
