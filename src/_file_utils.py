"""Internal file-system utilities."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def _atomic_write_text(path: Path, content: str) -> None:
    """Write text via a same-directory temporary file and atomic replacement."""
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(content)
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _atomic_write_json(path: Path, data: Any) -> None:
    """Serialize *data* as pretty UTF-8 JSON and write it atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
