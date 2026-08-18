"""Lightweight SQLite Database Layer for ResearchPilot Persistent Session History."""

import os
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = os.path.join(".", "data", "history.db")


def _get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize the research history table."""
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS research_history (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                mode TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                report TEXT NOT NULL,
                evidence_verification TEXT,
                documents TEXT,
                steps TEXT
            )
            """
        )
        conn.commit()


def save_session(
    query: str,
    mode: str,
    report: str,
    documents: List[Dict[str, Any]],
    evidence_verification: Optional[Dict[str, Any]] = None,
    steps: Optional[List[str]] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """Save a completed research session to the database."""
    init_db(db_path)
    session_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    docs_json = json.dumps(documents)
    verification_json = json.dumps(evidence_verification or {})
    steps_json = json.dumps(steps or [])

    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO research_history
            (id, query, mode, timestamp, report, evidence_verification, documents, steps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, query, mode, now_iso, report, verification_json, docs_json, steps_json),
        )
        conn.commit()

    return {
        "id": session_id,
        "query": query,
        "mode": mode,
        "timestamp": now_iso,
        "report": report,
        "evidence_verification": evidence_verification or {},
        "documents": documents,
        "steps": steps or [],
    }


def list_sessions(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """List all saved research sessions, ordered newest first."""
    init_db(db_path)
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, query, mode, timestamp, evidence_verification, documents, steps
            FROM research_history
            ORDER BY timestamp DESC
            """
        )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            docs = json.loads(r["documents"] or "[]")
            result.append(
                {
                    "id": r["id"],
                    "query": r["query"],
                    "mode": r["mode"],
                    "timestamp": r["timestamp"],
                    "source_count": len(docs),
                    "verification_status": json.loads(r["evidence_verification"] or "{}").get("status", "verified"),
                }
            )
        return result


def get_session(session_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve a single research session by ID."""
    init_db(db_path)
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, query, mode, timestamp, report, evidence_verification, documents, steps
            FROM research_history
            WHERE id = ?
            """,
            (session_id,),
        )
        r = cursor.fetchone()
        if not r:
            return None

        return {
            "id": r["id"],
            "query": r["query"],
            "mode": r["mode"],
            "timestamp": r["timestamp"],
            "report": r["report"],
            "evidence_verification": json.loads(r["evidence_verification"] or "{}"),
            "documents": json.loads(r["documents"] or "[]"),
            "steps": json.loads(r["steps"] or "[]"),
        }


def delete_session(session_id: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Delete a research session by ID."""
    init_db(db_path)
    with _get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM research_history WHERE id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0
