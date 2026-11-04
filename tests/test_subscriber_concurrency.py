from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import time

from src.storage import manager
from src.storage.manager import StorageManager


def test_concurrent_subscriber_updates_do_not_lose_addresses(tmp_path, monkeypatch):
    original_write = manager._atomic_write_text

    def delayed_write(path, content):
        # Widen the read/modify/write overlap, without delaying lock acquisition.
        time.sleep(0.02)
        original_write(path, content)

    monkeypatch.setattr(manager, "_atomic_write_text", delayed_write)
    managers = [StorageManager(str(tmp_path)) for _ in range(8)]
    start = Barrier(len(managers))

    def add(index):
        start.wait()
        managers[index].add_subscriber(f"reader{index}@example.com")

    with ThreadPoolExecutor(max_workers=len(managers)) as pool:
        list(pool.map(add, range(len(managers))))
    assert sorted(managers[0].load_subscribers()) == [f"reader{i}@example.com" for i in range(8)]
