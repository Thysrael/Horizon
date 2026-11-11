from __future__ import annotations

from pathlib import Path

import pytest

import src._file_utils as file_utils
from src.mcp.run_store import RunStore


def test_create_run_writes_meta(tmp_path: Path) -> None:
    store = RunStore(tmp_path)

    run_id = store.create_run()
    meta = store.load_meta(run_id)

    assert run_id.startswith("run-")
    assert meta["run_id"] == run_id
    assert "created_at" in meta


def test_create_run_rejects_existing_id_without_changing_artifacts(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-existing")
    store.save_items(run_id, "raw", [{"title": "original"}])
    store.save_items(run_id, "scored", [{"title": "scored"}])
    store.save_summary(run_id, "en", "original summary")
    original_meta = store.load_meta(run_id)

    with pytest.raises(FileExistsError):
        store.create_run(run_id)

    assert store.load_items(run_id, "raw") == [{"title": "original"}]
    assert store.load_items(run_id, "scored") == [{"title": "scored"}]
    assert store.load_summary(run_id, "en") == "original summary"
    assert store.load_meta(run_id) == original_meta


def test_save_and_load_stage_items(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-fixed")
    items = [{"title": "foo"}, {"title": "bar"}]

    path = store.save_items(run_id, "raw", items)
    loaded = store.load_items(run_id, "raw")

    assert path.name == "raw_items.json"
    assert loaded == items
    assert store.has_stage(run_id, "raw") is True


def test_update_meta_sets_updated_at(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-meta")

    meta = store.update_meta(run_id, {"status": "done"})

    assert meta["status"] == "done"
    assert "updated_at" in meta


def test_save_and_load_summary(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-summary")

    saved = store.save_summary(run_id, "zh", "# 摘要")
    content = store.load_summary(run_id, "zh")

    assert saved.name == "summary-zh.md"
    assert content == "# 摘要"


def test_saving_upstream_stage_invalidates_downstream_artifacts(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-invalidation")
    for stage in ("raw", "scored", "filtered", "enriched"):
        store.save_items(run_id, stage, [{"stage": stage}])
    store.save_summary(run_id, "en", "old summary")
    store.update_meta(
        run_id,
        {
            "scored_count": 2,
            "filtered_count": 1,
            "enrichment_status": "success",
            "summary_stage": "enriched",
        },
    )

    store.save_items(run_id, "scored", [{"stage": "new scored"}])

    assert store.has_stage(run_id, "raw") is True
    assert store.has_stage(run_id, "scored") is True
    assert store.has_stage(run_id, "filtered") is False
    assert store.has_stage(run_id, "enriched") is False
    with pytest.raises(FileNotFoundError):
        store.load_summary(run_id, "en")
    meta = store.load_meta(run_id)
    assert "scored_count" in meta
    assert "filtered_count" not in meta
    assert "enrichment_status" not in meta
    assert "summary_stage" not in meta


def test_unsupported_stage_raises(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-invalid-stage")

    with pytest.raises(ValueError, match="Unsupported stage"):
        store.save_items(run_id, "unknown", [])


def test_missing_run_raises(tmp_path: Path) -> None:
    store = RunStore(tmp_path)

    with pytest.raises(FileNotFoundError, match="Run not found"):
        store.run_dir("missing-run")


def test_rejects_path_traversal_run_id(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "runs")

    with pytest.raises(ValueError, match="Invalid run_id"):
        store.create_run("../outside")

    assert not (tmp_path / "outside").exists()


def test_rejects_unsafe_summary_language(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-summary-safe")

    with pytest.raises(ValueError, match="Invalid summary language"):
        store.save_summary(run_id, "../zh", "# unsafe")


def test_missing_artifact_raises(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-missing-file")

    with pytest.raises(FileNotFoundError, match="Artifact not found"):
        store.read_json(run_id, "does-not-exist.json")


def test_list_runs_returns_desc_order(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run1 = store.create_run("run-1")
    store.update_meta(run1, {"seq": 1})
    run2 = store.create_run("run-2")
    store.update_meta(run2, {"seq": 2})

    runs = store.list_runs(limit=10)

    assert runs[0]["run_id"] == "run-2"
    assert runs[1]["run_id"] == "run-1"


@pytest.mark.parametrize(
    ("filename", "save"),
    [
        ("raw_items.json", lambda store, run_id: store.save_items(run_id, "raw", [])),
        ("summary-en.md", lambda store, run_id: store.save_summary(run_id, "en", "new")),
    ],
)
def test_replace_failure_preserves_destination_and_cleans_temp(
    tmp_path: Path, monkeypatch, filename, save
) -> None:
    store = RunStore(tmp_path)
    run_id = store.create_run("run-atomic")
    destination = store.run_dir(run_id) / filename
    destination.write_text("existing", encoding="utf-8")

    def fail_replace(source, target):
        raise OSError("replace failed")

    monkeypatch.setattr(file_utils.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        save(store, run_id)

    assert destination.read_text(encoding="utf-8") == "existing"
    assert list(destination.parent.glob(f".{destination.name}.*.tmp")) == []
