"""SQLite 会话持久化。会话、规划单、微测试作答都随会话数据落库。"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.config import ROOT

DB_PATH = Path(os.environ.get("SICHE_DB_PATH", str(ROOT / "siche.db")))
_LOCK = threading.Lock()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sessions ("
        "id TEXT PRIMARY KEY, data TEXT NOT NULL, updated_at TEXT NOT NULL)"
    )
    return conn


def save(session: dict) -> dict:
    payload = json.dumps(session, ensure_ascii=False)
    now = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO sessions(id, data, updated_at) VALUES(?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET data=excluded.data, updated_at=excluded.updated_at",
                (session["id"], payload, now),
            )
            conn.commit()
        finally:
            conn.close()
    return session


def get(session_id: str) -> dict | None:
    with _LOCK:
        conn = _connect()
        try:
            row = conn.execute("SELECT data FROM sessions WHERE id=?", (session_id,)).fetchone()
        finally:
            conn.close()
    return json.loads(row[0]) if row else None


def clear() -> None:
    with _LOCK:
        conn = _connect()
        try:
            conn.execute("DELETE FROM sessions")
            conn.commit()
        finally:
            conn.close()
