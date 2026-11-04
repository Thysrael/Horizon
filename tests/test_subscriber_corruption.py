import pytest

from src.storage.manager import ConfigError, StorageManager


@pytest.mark.parametrize("operation", ["add_subscriber", "remove_subscriber"])
@pytest.mark.parametrize("content", ['{broken', 'null', '{}', '[42]', '"address"'])
def test_subscriber_updates_do_not_replace_corrupt_lists(tmp_path, content, operation):
    path = tmp_path / "subscribers.json"
    path.write_text(content, encoding="utf-8")
    storage = StorageManager(str(tmp_path))
    with pytest.raises(ConfigError, match="subscriber"):
        getattr(storage, operation)("reader@example.com")
    assert path.read_text(encoding="utf-8") == content


def test_missing_subscriber_file_starts_an_empty_list(tmp_path):
    storage = StorageManager(str(tmp_path))
    storage.add_subscriber("reader@example.com")
    assert storage.load_subscribers() == ["reader@example.com"]


def test_invalid_utf8_subscribers_are_preserved(tmp_path):
    path = tmp_path / "subscribers.json"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(ConfigError, match="subscriber"):
        StorageManager(str(tmp_path)).add_subscriber("reader@example.com")
    assert path.read_bytes() == b"\xff\xfe"
