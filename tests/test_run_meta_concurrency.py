from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import time

import src.mcp.run_store as module
from src.mcp.run_store import RunStore


def test_concurrent_metadata_updates_preserve_independent_fields(tmp_path, monkeypatch):
    stores = [RunStore(tmp_path) for _ in range(8)]
    run_id = stores[0].create_run("concurrent")
    original_write = module._atomic_write_text

    def delayed_write(path, content):
        time.sleep(0.02)
        original_write(path, content)

    monkeypatch.setattr(module, "_atomic_write_text", delayed_write)
    start = Barrier(len(stores))

    def update(index):
        start.wait()
        stores[index].update_meta(run_id, {f"field_{index}": index})

    with ThreadPoolExecutor(max_workers=len(stores)) as pool:
        list(pool.map(update, range(len(stores))))
    meta = stores[0].load_meta(run_id)
    assert all(meta.get(f"field_{i}") == i for i in range(len(stores)))
