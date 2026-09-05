"""LocalRegistry — the only HashRegistry implementation for this build (§8).

Backed by SQLite so authorizations survive a restart; falls back to a pure
in-memory dict when path=":memory:". Thread-safe for the FastAPI app.
"""
from __future__ import annotations

import sqlite3
import threading

from app.registry.base import HashRegistry
from app.schemas import ContentRecord


class LocalRegistry(HashRegistry):
    def __init__(self, path: str = ":memory:") -> None:
        # check_same_thread=False + a lock so it is safe under uvicorn workers.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS content_records (
                    content_id    TEXT PRIMARY KEY,
                    content_hash  TEXT NOT NULL,
                    authorized_by TEXT NOT NULL,
                    timestamp     TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    def authorize(self, record: ContentRecord) -> None:
        with self._lock:
            # Latest authorization for a content_id wins (re-authorization).
            self._conn.execute(
                """
                INSERT INTO content_records
                    (content_id, content_hash, authorized_by, timestamp)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(content_id) DO UPDATE SET
                    content_hash  = excluded.content_hash,
                    authorized_by = excluded.authorized_by,
                    timestamp     = excluded.timestamp
                """,
                (
                    record.content_id,
                    record.content_hash,
                    record.authorized_by,
                    record.timestamp.isoformat(),
                ),
            )
            self._conn.commit()

    def get_authorized_hash(self, content_id: str) -> str | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT content_hash FROM content_records WHERE content_id = ?",
                (content_id,),
            ).fetchone()
        return row[0] if row else None
