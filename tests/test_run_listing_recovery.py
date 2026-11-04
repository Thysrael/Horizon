import pytest

from src.mcp.run_store import RunStore


@pytest.mark.parametrize("broken", [b"[]", b"null", b"42", b"{oops", b"\xff\xfe", b'{"updated_at": []}'])
def test_corrupt_run_metadata_does_not_hide_healthy_runs(tmp_path, broken):
    store = RunStore(tmp_path)
    good = store.create_run("healthy")
    bad_dir = tmp_path / "broken"
    bad_dir.mkdir()
    (bad_dir / "meta.json").write_bytes(broken)
    assert [run["run_id"] for run in store.list_runs()] == [good]


def test_unreadable_run_metadata_does_not_hide_healthy_runs(tmp_path, monkeypatch):
    from pathlib import Path
    store = RunStore(tmp_path)
    store.create_run("healthy")
    store.create_run("unreadable")
    original = Path.read_text

    def read(path, *args, **kwargs):
        if path.parent.name == "unreadable":
            raise OSError("metadata disappeared during listing")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    assert [run["run_id"] for run in store.list_runs()] == ["healthy"]
