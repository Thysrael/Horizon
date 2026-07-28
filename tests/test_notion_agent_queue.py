from __future__ import annotations

from pathlib import Path

from src.notion_agent.queue import EventQueue


def test_queue_deduplicates_and_finishes_events(tmp_path: Path) -> None:
    queue = EventQueue(tmp_path / "events.sqlite3")
    payload = {"id": "event-1", "type": "page.properties_updated"}

    assert queue.enqueue(
        event_id="event-1",
        event_type="page.properties_updated",
        page_id="page-1",
        payload=payload,
    )
    assert not queue.enqueue(
        event_id="event-1",
        event_type="page.properties_updated",
        page_id="page-1",
        payload=payload,
    )

    job = queue.claim_next()

    assert job is not None
    assert job.event_id == "event-1"
    assert job.page_id == "page-1"
    assert job.attempts == 1
    assert job.payload == payload
    queue.finish(job.event_id, "succeeded", "done")
    assert queue.counts() == {
        "queued": 0,
        "running": 0,
        "succeeded": 1,
        "ignored": 0,
        "failed": 0,
    }
    assert queue.claim_next() is None


def test_queue_recovers_interrupted_event(tmp_path: Path) -> None:
    queue = EventQueue(tmp_path / "events.sqlite3")
    queue.enqueue(
        event_id="event-2",
        event_type="page.created",
        page_id="page-2",
        payload={"id": "event-2"},
    )
    assert queue.claim_next() is not None

    assert queue.recover_interrupted() == 1
    recovered = queue.claim_next()

    assert recovered is not None
    assert recovered.event_id == "event-2"
    assert recovered.attempts == 2
