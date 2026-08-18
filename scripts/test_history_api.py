"""Test script for Research History API endpoints and database storage."""

import urllib.request
import json
from shared import history_db

print("1. Direct History Database Save & Retrieval...")
saved = history_db.save_session(
    query="How does state persistence work in LangGraph using checkpointers?",
    mode="hybrid",
    report="# Technical Research Report: LangGraph State Persistence\n\nCheckpointers serialize graph state snapshot...",
    documents=[
        {"title": "LangGraph Persistence Conceptual Guide", "url": "https://langchain-ai.github.io/langgraph/concepts/persistence/", "source": "knowledge_base"},
        {"title": "LangGraph API Reference", "url": "https://langchain-ai.github.io/langgraph/reference/", "source": "web_search"}
    ],
    evidence_verification={"status": "supported", "summary": "Directly supported across sources"},
    steps=["Investigate checkpointer interface", "Analyze SQLite/Postgres checkpointers"]
)

session_id = saved["id"]
print(f"   Saved session ID: {session_id}")

print("\n2. Testing GET /api/history via HTTP...")
req = urllib.request.Request("http://127.0.0.1:8000/api/history")
with urllib.request.urlopen(req) as resp:
    history = json.loads(resp.read().decode("utf-8"))
    print(f"   GET /api/history returned {len(history)} session(s)")
    assert len(history) >= 1
    assert history[0]["id"] == session_id

print(f"\n3. Testing GET /api/history/{session_id} via HTTP...")
req = urllib.request.Request(f"http://127.0.0.1:8000/api/history/{session_id}")
with urllib.request.urlopen(req) as resp:
    detail = json.loads(resp.read().decode("utf-8"))
    print(f"   GET /api/history/{session_id} returned query: '{detail.get('query')}'")
    assert detail["report"].startswith("# Technical Research Report")
    assert len(detail["documents"]) == 2

print(f"\n4. Testing DELETE /api/history/{session_id} via HTTP...")
req = urllib.request.Request(f"http://127.0.0.1:8000/api/history/{session_id}", method="DELETE")
with urllib.request.urlopen(req) as resp:
    del_res = json.loads(resp.read().decode("utf-8"))
    print(f"   DELETE /api/history/{session_id} returned status: {del_res.get('status')}")
    assert del_res["status"] == "success"

print("\n5. Verifying deletion via GET /api/history...")
req = urllib.request.Request("http://127.0.0.1:8000/api/history")
with urllib.request.urlopen(req) as resp:
    history_after = json.loads(resp.read().decode("utf-8"))
    assert not any(h["id"] == session_id for h in history_after)
    print("   Session successfully purged from history database!")

print("\n=========================================================")
print("          History API Integration Test PASSED 100%       ")
print("=========================================================")
