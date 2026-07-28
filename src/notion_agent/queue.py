"""SQLite-backed durable webhook event queue."""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class EventJob:
    event_id: str
    event_type: str
    page_id: str
    payload: dict[str, Any]
    attempts: int


class EventQueue:
    """A single-consumer queue with durable deduplication by Notion event ID."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS webhook_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    page_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (
                        state IN (
                            'queued',
                            'running',
                            'succeeded',
                            'ignored',
                            'failed'
                        )
                    ),
                    attempts INTEGER NOT NULL DEFAULT 0,
                    execution_id TEXT NOT NULL DEFAULT '',
                    result TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS webhook_events_state_created
                ON webhook_events(state, created_at)
                """
            )

    def enqueue(
        self,
        *,
        event_id: str,
        event_type: str,
        page_id: str,
        payload: Mapping[str, Any],
    ) -> bool:
        serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        timestamp = _now()
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO webhook_events (
                    event_id,
                    event_type,
                    page_id,
                    payload,
                    state,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, 'queued', ?, ?)
                """,
                (
                    event_id,
                    event_type,
                    page_id,
                    serialized,
                    timestamp,
                    timestamp,
                ),
            )
            return cursor.rowcount == 1

    def recover_interrupted(self) -> int:
        timestamp = _now()
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE webhook_events
                SET state = 'queued',
                    result = 'Recovered after listener restart',
                    updated_at = ?
                WHERE state = 'running'
                """,
                (timestamp,),
            )
            return cursor.rowcount

    def claim_next(self) -> EventJob | None:
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT event_id, event_type, page_id, payload, attempts
                FROM webhook_events
                WHERE state = 'queued'
                ORDER BY created_at ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                connection.commit()
                return None

            attempts = int(row["attempts"]) + 1
            execution_id = f"local-{row['event_id']}"
            connection.execute(
                """
                UPDATE webhook_events
                SET state = 'running',
                    attempts = ?,
                    execution_id = ?,
                    updated_at = ?
                WHERE event_id = ?
                """,
                (attempts, execution_id, _now(), row["event_id"]),
            )
            connection.commit()
            return EventJob(
                event_id=str(row["event_id"]),
                event_type=str(row["event_type"]),
                page_id=str(row["page_id"]),
                payload=json.loads(str(row["payload"])),
                attempts=attempts,
            )

    def finish(self, event_id: str, state: str, result: str = "") -> None:
        if state not in {"succeeded", "ignored", "failed"}:
            raise ValueError(f"Invalid terminal queue state: {state}")
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE webhook_events
                SET state = ?, result = ?, updated_at = ?
                WHERE event_id = ? AND state = 'running'
                """,
                (state, result[:4_000], _now(), event_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError(
                    f"Queue event {event_id!r} is not in the running state"
                )

    def counts(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT state, COUNT(*) AS count
                FROM webhook_events
                GROUP BY state
                """
            ).fetchall()
        counts = {
            "queued": 0,
            "running": 0,
            "succeeded": 0,
            "ignored": 0,
            "failed": 0,
        }
        counts.update({str(row["state"]): int(row["count"]) for row in rows})
        return counts
