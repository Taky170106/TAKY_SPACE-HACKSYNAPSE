"""AuditStore — append-only persistence for AuditRecords (Phase 4, §11).

SQLite-backed and thread-safe, mirroring LocalRegistry so it is safe under
uvicorn workers. Append-only: records are inserted, never updated or deleted —
an audit trail you can edit is not an audit trail.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime

from app.audit.records import AuditRecord


class AuditStore:
    def __init__(self, path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_records (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp           TEXT NOT NULL,
                    device_id           TEXT NOT NULL,
                    content_id          TEXT,
                    verified_match      INTEGER,
                    verification_action TEXT,
                    risk_score          INTEGER,
                    risk_level          TEXT,
                    decision            TEXT NOT NULL,
                    recommended_action  TEXT NOT NULL,
                    reasons             TEXT NOT NULL,
                    event_count         INTEGER NOT NULL
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_device "
                "ON audit_records (device_id)"
            )
            self._conn.commit()

    def record(self, rec: AuditRecord) -> AuditRecord:
        """Persist an AuditRecord and return it with its assigned `id`."""
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT INTO audit_records
                    (timestamp, device_id, content_id, verified_match,
                     verification_action, risk_score, risk_level, decision,
                     recommended_action, reasons, event_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec.timestamp.isoformat(),
                    rec.device_id,
                    rec.content_id,
                    None if rec.verified_match is None else int(rec.verified_match),
                    rec.verification_action,
                    rec.risk_score,
                    rec.risk_level,
                    rec.decision,
                    rec.recommended_action,
                    json.dumps(rec.reasons),
                    rec.event_count,
                ),
            )
            self._conn.commit()
            rec.id = cur.lastrowid
        return rec

    def list(
        self, *, device_id: str | None = None, limit: int = 100
    ) -> list[AuditRecord]:
        """Return recent records (newest first), optionally filtered by device."""
        query = "SELECT * FROM audit_records"
        params: list[object] = []
        if device_id is not None:
            query += " WHERE device_id = ?"
            params.append(device_id)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_record(r) for r in rows]

    def count(self) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM audit_records"
            ).fetchone()
        return int(row[0])

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> AuditRecord:
        return AuditRecord(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            device_id=row["device_id"],
            content_id=row["content_id"],
            verified_match=None
            if row["verified_match"] is None
            else bool(row["verified_match"]),
            verification_action=row["verification_action"],
            risk_score=row["risk_score"],
            risk_level=row["risk_level"],
            decision=row["decision"],
            recommended_action=row["recommended_action"],
            reasons=json.loads(row["reasons"]),
            event_count=row["event_count"],
        )
