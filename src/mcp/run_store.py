"""Run artifact persistence for Horizon MCP."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .._file_utils import _atomic_write_text


logger = logging.getLogger(__name__)


STAGES = {
    "raw": "raw_items.json",
    "scored": "scored_items.json",
    "filtered": "filtered_items.json",
    "enriched": "enriched_items.json",
}
STAGE_ORDER = tuple(STAGES)
_META_PREFIXES = {
    "scored": ("scored_", "selected_count"),
    "filtered": ("filtered_", "filter_", "topic_", "balanced_"),
    "enriched": ("enrichment_", "enriched_", "citation_count"),
    "summary": ("summary_",),
}
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
LANGUAGE_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass
class RunStore:
    """Store intermediate artifacts per pipeline run."""

    root: Path

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def create_run(self, run_id: str | None = None) -> str:
        run_id = run_id or self._make_run_id()
        run_dir = self._run_path(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        meta_path = run_dir / "meta.json"
        if not meta_path.exists():
            self.write_json(
                run_id, "meta.json", {"run_id": run_id, "created_at": self._utc_now()}
            )
        return run_id

    def run_dir(self, run_id: str) -> Path:
        path = self._run_path(run_id)
        if not path.exists():
            raise FileNotFoundError(f"Run not found: {run_id}")
        return path

    def has_stage(self, run_id: str, stage: str) -> bool:
        return (self.run_dir(run_id) / self._stage_file(stage)).exists()

    def save_items(self, run_id: str, stage: str, items: list[dict[str, Any]]) -> Path:
        path = self.write_json(run_id, self._stage_file(stage), items)
        self.invalidate_after(run_id, stage)
        return path

    def invalidate_after(self, run_id: str, stage: str) -> None:
        """Remove artifacts derived from the newly saved stage."""
        try:
            stage_index = STAGE_ORDER.index(stage)
        except ValueError as exc:
            raise ValueError(f"Unsupported stage: {stage}") from exc
        run_dir = self.run_dir(run_id)
        for downstream in STAGE_ORDER[stage_index + 1 :]:
            (run_dir / STAGES[downstream]).unlink(missing_ok=True)
        for summary_path in run_dir.glob("summary-*.md"):
            summary_path.unlink()
        self._invalidate_meta(run_id, (*STAGE_ORDER[stage_index + 1 :], "summary"))

    def invalidate_from(self, run_id: str, stage: str) -> None:
        """Remove a stage and every artifact derived from it."""
        try:
            stage_index = STAGE_ORDER.index(stage)
        except ValueError as exc:
            raise ValueError(f"Unsupported stage: {stage}") from exc
        run_dir = self.run_dir(run_id)
        for invalidated in STAGE_ORDER[stage_index:]:
            (run_dir / STAGES[invalidated]).unlink(missing_ok=True)
        for summary_path in run_dir.glob("summary-*.md"):
            summary_path.unlink()
        self._invalidate_meta(run_id, (*STAGE_ORDER[stage_index:], "summary"))

    def _invalidate_meta(self, run_id: str, stages: tuple[str, ...]) -> None:
        prefixes = tuple(
            prefix
            for stage in stages
            for prefix in _META_PREFIXES.get(stage, ())
        )
        meta = self.load_meta(run_id)
        cleaned = {
            key: value
            for key, value in meta.items()
            if not key.startswith(prefixes)
        }
        if cleaned != meta:
            self.write_json(run_id, "meta.json", cleaned)

    def load_items(self, run_id: str, stage: str) -> list[dict[str, Any]]:
        return self.read_json(run_id, self._stage_file(stage))

    def save_summary(self, run_id: str, language: str, markdown: str) -> Path:
        filename = self._summary_file(language)
        path = self.run_dir(run_id) / filename
        _atomic_write_text(path, markdown)
        return path

    def load_summary(self, run_id: str, language: str) -> str:
        path = self.run_dir(run_id) / self._summary_file(language)
        if not path.exists():
            raise FileNotFoundError(f"Summary not found: run={run_id} lang={language}")
        return path.read_text(encoding="utf-8")

    def update_meta(self, run_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        meta = self.read_json(run_id, "meta.json")
        meta.update(updates)
        meta["updated_at"] = self._utc_now()
        self.write_json(run_id, "meta.json", meta)
        return meta

    def load_meta(self, run_id: str) -> dict[str, Any]:
        return self.read_json(run_id, "meta.json")

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        """List runs sorted by create/update time descending."""

        entries: list[dict[str, Any]] = []
        for run_dir in self.root.iterdir():
            if not run_dir.is_dir():
                continue
            meta_path = run_dir / "meta.json"
            if not meta_path.exists():
                continue
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                logger.warning("Could not read run metadata %s: %s", run_dir.name, exc)
                continue
            if not isinstance(meta, dict) or any(
                key in meta and not isinstance(meta[key], str)
                for key in ("created_at", "updated_at")
            ):
                logger.warning("Skipping invalid run metadata: %s", run_dir.name)
                continue

            created = meta.get("created_at") or ""
            updated = meta.get("updated_at") or created
            entries.append(
                {
                    "run_id": meta.get("run_id", run_dir.name),
                    "created_at": created,
                    "updated_at": updated,
                    "meta": meta,
                }
            )

        entries.sort(key=lambda x: x["updated_at"] or x["created_at"], reverse=True)
        return entries[: max(0, limit)]

    def write_json(self, run_id: str, filename: str, payload: Any) -> Path:
        path = self.run_dir(run_id) / filename
        _atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))
        return path

    def read_json(self, run_id: str, filename: str) -> Any:
        path = self.run_dir(run_id) / filename
        if not path.exists():
            raise FileNotFoundError(f"Artifact not found: run={run_id} file={filename}")
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _stage_file(stage: str) -> str:
        if stage not in STAGES:
            supported = ", ".join(sorted(STAGES))
            raise ValueError(
                f"Unsupported stage '{stage}', expected one of: {supported}"
            )
        return STAGES[stage]

    def _run_path(self, run_id: str) -> Path:
        if not RUN_ID_RE.fullmatch(run_id) or ".." in run_id:
            raise ValueError("Invalid run_id")

        root = self.root.resolve()
        path = (self.root / run_id).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Invalid run_id")
        return path

    @staticmethod
    def _summary_file(language: str) -> str:
        if not LANGUAGE_RE.fullmatch(language):
            raise ValueError("Invalid summary language")
        return f"summary-{language}.md"

    @staticmethod
    def _make_run_id() -> str:
        now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"run-{now}-{uuid4().hex[:8]}"

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()
