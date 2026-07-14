"""
SQLite persistence for user accounts and research chat history.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from werkzeug.security import check_password_hash, generate_password_hash

from config import Config

DB_PATH = Path(Config.DATABASE_PATH)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                agent_session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                question TEXT NOT NULL,
                report_text TEXT,
                results_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_chat_history_user
                ON chat_history(user_id, updated_at DESC);
            """
        )
        conn.commit()


def create_user(username: str, password: str) -> Optional[int]:
    username = username.strip().lower()
    if not username or not password:
        return None

    with get_connection() as conn:
        try:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), _utc_now()),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_username(username)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def save_chat_history(
    user_id: int,
    agent_session_id: str,
    question: str,
    results_data: Dict[str, Any],
) -> int:
    title = (question or "Untitled research")[:80]
    report_text = results_data.get("report", "")
    payload = json.dumps(results_data, default=str)

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM chat_history WHERE user_id = ? AND agent_session_id = ?",
            (user_id, agent_session_id),
        ).fetchone()

        now = _utc_now()
        if existing:
            conn.execute(
                """
                UPDATE chat_history
                SET title = ?, question = ?, report_text = ?, results_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, question, report_text, payload, now, existing["id"]),
            )
            conn.commit()
            return existing["id"]

        cursor = conn.execute(
            """
            INSERT INTO chat_history
                (user_id, agent_session_id, title, question, report_text, results_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, agent_session_id, title, question, report_text, payload, now, now),
        )
        conn.commit()
        return cursor.lastrowid


def list_chat_history(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, agent_session_id, title, question, created_at, updated_at
            FROM chat_history
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def get_chat_history(user_id: int, history_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, agent_session_id, title, question, report_text, results_json, created_at, updated_at
            FROM chat_history
            WHERE id = ? AND user_id = ?
            """,
            (history_id, user_id),
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        if data.get("results_json"):
            data["results"] = json.loads(data["results_json"])
        return data


def get_chat_by_agent_session(user_id: int, agent_session_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, user_id, agent_session_id, title, question, report_text, results_json, created_at, updated_at
            FROM chat_history
            WHERE user_id = ? AND agent_session_id = ?
            """,
            (user_id, agent_session_id),
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        if data.get("results_json"):
            data["results"] = json.loads(data["results_json"])
        return data


def delete_chat_history(user_id: int, history_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM chat_history WHERE id = ? AND user_id = ?",
            (history_id, user_id),
        )
        conn.commit()
        return cursor.rowcount > 0
