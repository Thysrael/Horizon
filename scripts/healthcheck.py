"""Container health probe with no credential output.

The probe first verifies that PostgreSQL accepts a query.  Application roles
also need a recently refreshed row in ``app_heartbeats``; this catches a live
but stuck bot, scheduler, or worker process.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def check(database_url: str, role: str | None, max_age_seconds: int) -> bool:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            if role:
                result = await connection.execute(
                    text(
                        "SELECT recorded_at >= now() - (:max_age * interval '1 second') "
                        "FROM app_heartbeats WHERE role = :role"
                    ),
                    {"role": role, "max_age": max_age_seconds},
                )
                return result.scalar_one_or_none() is True
        return True
    except Exception:
        # Database URLs contain passwords, so errors deliberately stay private.
        return False
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check InfoService process health")
    parser.add_argument("--role", choices=("bot", "scheduler", "worker"))
    parser.add_argument("--max-age-seconds", type=int, default=120)
    args = parser.parse_args()
    database_url = os.getenv("DATABASE_URL")
    if not database_url or args.max_age_seconds < 1:
        return 1
    return 0 if asyncio.run(check(database_url, args.role, args.max_age_seconds)) else 1


if __name__ == "__main__":
    sys.exit(main())
