"""FastAPI Backend Server for ResearchPilot Dashboard with Persistent Session History."""

import json
import asyncio
import os
from typing import Literal, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig

from index_graph import graph as index_graph
from retrieval_graph import graph as retrieval_graph
from shared import history_db

load_dotenv()
history_db.init_db()

app = FastAPI(title="ResearchPilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    query: str
    mode: Literal["hybrid", "knowledge_base", "web_research"] = "hybrid"


@app.get("/api/health")
def health_check():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    has_key = bool(api_key and api_key != "your_gemini_api_key_here")
    return {"status": "ok", "gemini_api_key_configured": has_key}


@app.get("/api/history")
def get_history():
    """Retrieve list of completed research sessions."""
    try:
        return history_db.list_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")


@app.get("/api/history/{session_id}")
def get_history_detail(session_id: str):
    """Retrieve details for a single research session."""
    session = history_db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")
    return session


@app.delete("/api/history/{session_id}")
def delete_history_session(session_id: str):
    """Delete a research session by ID."""
    deleted = history_db.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Research session not found")
    return {"status": "success", "id": session_id}


def _ensure_env():
    load_dotenv(override=True)
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    google_key = os.environ.get("GOOGLE_API_KEY", "").strip()

    if gemini_key and gemini_key != "your_gemini_api_key_here":
        os.environ["GOOGLE_API_KEY"] = gemini_key
        os.environ["GEMINI_API_KEY"] = gemini_key
    elif google_key and google_key != "your_gemini_api_key_here":
        os.environ["GEMINI_API_KEY"] = google_key
        os.environ["GOOGLE_API_KEY"] = google_key
    else:
        raise HTTPException(
            status_code=400,
            detail="Missing valid GEMINI_API_KEY. Please paste your Gemini API key into the .env file.",
        )


@app.post("/api/research/stream")
async def stream_research(request: ResearchRequest):
    query_str = request.query.strip() if request.query else ""
    if not query_str:
        raise HTTPException(status_code=400, detail="Research question cannot be empty.")
    if len(query_str) > 2000:
        raise HTTPException(status_code=400, detail="Research question exceeds maximum length of 2000 characters.")

    _ensure_env()

    enable_web = request.mode in ("hybrid", "web_research")
    config = RunnableConfig(
        configurable={
            "retriever_provider": "chroma",
            "enable_web_search": enable_web,
            "embedding_model": "google_genai/gemini-embedding-001",
        }
    )

    async def event_generator():
        try:
            yield f"data: {json.dumps({'event': 'stage', 'stage': 'analysis', 'status': 'running'})}\n\n"
            await asyncio.sleep(0.2)

            try:
                await index_graph.ainvoke({}, config=config)
            except Exception:
                pass

            yield f"data: {json.dumps({'event': 'stage', 'stage': 'analysis', 'status': 'completed'})}\n\n"

            yield f"data: {json.dumps({'event': 'stage', 'stage': 'planning', 'status': 'running'})}\n\n"

            result = await retrieval_graph.ainvoke(
                {"messages": [("user", request.query)]}, config=config
            )

            router = result.get("router", {})
            steps = result.get("steps", [])
            docs = result.get("documents", [])
            verification = result.get("evidence_verification", {})

            yield f"data: {json.dumps({'event': 'stage', 'stage': 'planning', 'status': 'completed', 'tasks': steps})}\n\n"

            yield f"data: {json.dumps({'event': 'stage', 'stage': 'tasks', 'status': 'running'})}\n\n"
            await asyncio.sleep(0.1)
            yield f"data: {json.dumps({'event': 'stage', 'stage': 'tasks', 'status': 'completed', 'tasks': steps})}\n\n"

            yield f"data: {json.dumps({'event': 'stage', 'stage': 'retrieval', 'status': 'running'})}\n\n"

            formatted_docs = []
            for doc in docs:
                formatted_docs.append(
                    {
                        "title": doc.metadata.get("title", "Untitled Document"),
                        "url": doc.metadata.get("url", doc.metadata.get("id", "#")),
                        "source": doc.metadata.get("source", "knowledge_base"),
                        "snippet": doc.page_content[:300],
                    }
                )

            yield f"data: {json.dumps({'event': 'stage', 'stage': 'retrieval', 'status': 'completed', 'source_count': len(formatted_docs)})}\n\n"

            yield f"data: {json.dumps({'event': 'stage', 'stage': 'verification', 'status': 'running'})}\n\n"
            await asyncio.sleep(0.1)
            yield f"data: {json.dumps({'event': 'stage', 'stage': 'verification', 'status': 'completed', 'verification': verification})}\n\n"

            yield f"data: {json.dumps({'event': 'stage', 'stage': 'synthesis', 'status': 'running'})}\n\n"

            last_msg = ""
            if result.get("messages"):
                raw_content = result["messages"][-1].content
                if isinstance(raw_content, str):
                    last_msg = raw_content
                elif isinstance(raw_content, list):
                    parts = []
                    for item in raw_content:
                        if isinstance(item, str):
                            parts.append(item)
                        elif isinstance(item, dict) and item.get("type") == "text":
                            parts.append(item.get("text", ""))
                        elif isinstance(item, dict) and "text" in item:
                            parts.append(str(item["text"]))
                        elif hasattr(item, "text"):
                            parts.append(getattr(item, "text"))
                    last_msg = "".join(parts) if parts else str(raw_content)
                else:
                    last_msg = str(raw_content)

            # Persist session to history SQLite database
            saved = history_db.save_session(
                query=request.query,
                mode=request.mode,
                report=last_msg,
                documents=formatted_docs,
                evidence_verification=verification,
                steps=steps,
            )

            complete_payload = {
                "event": "complete",
                "stage": "synthesis",
                "status": "completed",
                "session_id": saved["id"],
                "query": request.query,
                "mode": request.mode,
                "router": router,
                "steps": steps,
                "evidence_verification": verification,
                "documents": formatted_docs,
                "report": last_msg,
            }
            yield f"data: {json.dumps(complete_payload)}\n\n"

        except Exception as e:
            print(f"[Server Error] SSE Research failed: {e}")
            yield f"data: {json.dumps({'event': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/research")
async def execute_research(request: ResearchRequest):
    query_str = request.query.strip() if request.query else ""
    if not query_str:
        raise HTTPException(status_code=400, detail="Research question cannot be empty.")
    if len(query_str) > 2000:
        raise HTTPException(status_code=400, detail="Research question exceeds maximum length of 2000 characters.")

    _ensure_env()

    enable_web = request.mode in ("hybrid", "web_research")
    config = RunnableConfig(
        configurable={
            "retriever_provider": "chroma",
            "enable_web_search": enable_web,
            "embedding_model": "google_genai/gemini-embedding-001",
        }
    )

    try:
        try:
            await index_graph.ainvoke({}, config=config)
        except Exception:
            pass

        result = await retrieval_graph.ainvoke(
            {"messages": [("user", request.query)]}, config=config
        )

        router = result.get("router", {})
        steps = result.get("steps", [])
        docs = result.get("documents", [])
        verification = result.get("evidence_verification", {})

        last_msg = ""
        if result.get("messages"):
            raw_content = result["messages"][-1].content
            if isinstance(raw_content, str):
                last_msg = raw_content
            elif isinstance(raw_content, list):
                parts = []
                for item in raw_content:
                    if isinstance(item, str):
                        parts.append(item)
                    elif isinstance(item, dict) and item.get("type") == "text":
                        parts.append(item.get("text", ""))
                    elif isinstance(item, dict) and "text" in item:
                        parts.append(str(item["text"]))
                    elif hasattr(item, "text"):
                        parts.append(getattr(item, "text"))
                last_msg = "".join(parts) if parts else str(raw_content)
            else:
                last_msg = str(raw_content)

        formatted_docs = []
        for doc in docs:
            formatted_docs.append(
                {
                    "title": doc.metadata.get("title", "Untitled Document"),
                    "url": doc.metadata.get("url", doc.metadata.get("id", "#")),
                    "source": doc.metadata.get("source", "knowledge_base"),
                    "snippet": doc.page_content[:300],
                }
            )

        saved = history_db.save_session(
            query=request.query,
            mode=request.mode,
            report=last_msg,
            documents=formatted_docs,
            evidence_verification=verification,
            steps=steps,
        )

        return {
            "id": saved["id"],
            "query": request.query,
            "mode": request.mode,
            "router": router,
            "steps": steps,
            "evidence_verification": verification,
            "documents": formatted_docs,
            "report": last_msg,
        }
    except Exception as e:
        print(f"[Server Error] Research execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

