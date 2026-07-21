"""Small, credential-free liveness records for container health checks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.infoservice.db.models import AppHeartbeat


async def touch_heartbeat(session_factory: Any, role: str) -> None:
    """Record a process heartbeat without logging connection information."""
    async with session_factory.begin() as session:
        heartbeat = await session.get(AppHeartbeat, role)
        if heartbeat is None:
            session.add(AppHeartbeat(role=role, recorded_at=datetime.now(timezone.utc)))
        else:
            heartbeat.recorded_at = datetime.now(timezone.utc)
