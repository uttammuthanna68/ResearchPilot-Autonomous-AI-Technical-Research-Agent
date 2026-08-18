"""Unit tests for the SQLite Research History database module."""

import os
import tempfile
import pytest

from shared.history_db import (
    init_db,
    save_session,
    list_sessions,
    get_session,
    delete_session,
)


@pytest.fixture
def temp_db():
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "test_history.db")
    init_db(db_path)
    yield db_path
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(tmp_dir)
    except Exception:
        pass


def test_save_and_get_session(temp_db):
    """Test saving a research session and retrieving it by ID."""
    session = save_session(
        query="How does state persistence work in LangGraph?",
        mode="hybrid",
        report="# Technical Research Report: LangGraph State Persistence",
        documents=[{"title": "Checkpointer Guide", "url": "https://langchain.com", "source": "knowledge_base"}],
        evidence_verification={"status": "supported", "summary": "Directly supported"},
        steps=["Investigate checkpointers"],
        db_path=temp_db,
    )

    assert "id" in session
    saved_id = session["id"]

    retrieved = get_session(saved_id, db_path=temp_db)
    assert retrieved is not None
    assert retrieved["query"] == "How does state persistence work in LangGraph?"
    assert retrieved["mode"] == "hybrid"
    assert retrieved["report"] == "# Technical Research Report: LangGraph State Persistence"
    assert len(retrieved["documents"]) == 1
    assert retrieved["documents"][0]["title"] == "Checkpointer Guide"
    assert retrieved["evidence_verification"]["status"] == "supported"


def test_list_sessions(temp_db):
    """Test listing multiple saved research sessions."""
    save_session(query="Query A", mode="hybrid", report="Report A", documents=[], db_path=temp_db)
    save_session(query="Query B", mode="knowledge_base", report="Report B", documents=[{}, {}], db_path=temp_db)

    sessions = list_sessions(db_path=temp_db)
    assert len(sessions) == 2
    assert sessions[0]["query"] == "Query B"  # Newest first
    assert sessions[1]["query"] == "Query A"
    assert sessions[0]["source_count"] == 2


def test_delete_session(temp_db):
    """Test deleting a research session by ID."""
    session = save_session(query="To be deleted", mode="hybrid", report="Delete me", documents=[], db_path=temp_db)
    saved_id = session["id"]

    assert get_session(saved_id, db_path=temp_db) is not None

    deleted = delete_session(saved_id, db_path=temp_db)
    assert deleted is True

    assert get_session(saved_id, db_path=temp_db) is None


def test_no_secrets_in_session(temp_db):
    """Verify that sessions do not leak or store API keys or secrets."""
    session = save_session(
        query="Security check",
        mode="hybrid",
        report="Report text",
        documents=[],
        evidence_verification={},
        db_path=temp_db,
    )

    retrieved = get_session(session["id"], db_path=temp_db)
    retrieved_str = str(retrieved)
    assert "GEMINI_API_KEY" not in retrieved_str
    assert "GOOGLE_API_KEY" not in retrieved_str
    assert "TAVILY_API_KEY" not in retrieved_str
