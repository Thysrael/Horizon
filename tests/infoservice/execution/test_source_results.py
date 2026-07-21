from types import SimpleNamespace
from uuid import uuid4

from src.infoservice.execution.service import _source_result_payloads


def test_aggregate_rss_outcome_is_persisted_for_every_configured_rss_source():
    sources = [
        SimpleNamespace(id=uuid4(), source_type="rss", enabled=True, display_name="Product feed"),
        SimpleNamespace(id=uuid4(), source_type="rss", enabled=True, display_name="Security feed"),
        SimpleNamespace(id=uuid4(), source_type="github", enabled=True, display_name="Repos"),
    ]
    outcomes = [
        {"source": "RSS Feeds", "status": "failure", "item_count": 7, "error": "upstream sk-private-key"},
        {"source": "GitHub", "status": "success", "item_count": 3},
    ]

    rows = _source_result_payloads(sources, outcomes)

    assert {(row.source_id, row.status, row.items_found) for row in rows} == {
        (sources[0].id, "failed", 0),
        (sources[1].id, "failed", 0),
        (sources[2].id, "succeeded", 3),
    }
    assert all("sk-private-key" not in (row.error_summary or "") for row in rows)
