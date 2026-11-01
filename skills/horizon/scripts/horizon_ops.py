#!/usr/bin/env python3
"""Call Horizon's staged service from any skill-compatible agent."""

from __future__ import annotations

import argparse
import asyncio
from contextlib import redirect_stdout
import inspect
import json
import os
from pathlib import Path
import sys
from typing import Any


# Keep native method names and parameters: the service owns the API contract.
OPERATIONS = (
    "validate_config", "fetch_items", "score_items", "filter_items",
    "enrich_items", "generate_summary", "run_pipeline", "list_runs",
    "get_run_meta", "get_run_stage", "get_run_summary",
)


def find_checkout(explicit: str | None) -> Path:
    requested = explicit or os.environ.get("HORIZON_PATH")
    candidates = (
        [Path(requested).expanduser()]
        if requested
        else [Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents]
    )
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file() and (candidate / "src/mcp/service.py").is_file():
            return candidate.resolve()
    raise FileNotFoundError("Set --horizon-path or HORIZON_PATH to a Horizon checkout.")


def repo_path(repo: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else repo / path).resolve()


async def call_service(args: argparse.Namespace, repo: Path) -> Any:
    # The script remains usable when installed outside the Horizon checkout.
    sys.path.insert(0, str(repo))
    from src.mcp.service import HorizonPipelineService

    runs_root = repo_path(repo, args.runs_root or "data/mcp-runs")
    service = HorizonPipelineService(runs_root=runs_root)
    method = getattr(service, args.operation)
    signature = inspect.signature(method)
    if args.describe:
        return {"signature": str(signature), "description": inspect.getdoc(method)}

    text = Path(args.params_file).read_text(encoding="utf-8") if args.params_file else args.params
    params = json.loads(text or "{}")
    if not isinstance(params, dict):
        raise ValueError("Parameters must be a JSON object.")
    if "horizon_path" in signature.parameters:
        if params.get("horizon_path") and repo_path(repo, params["horizon_path"]) != repo:
            raise ValueError("Use --horizon-path to select the checkout, consistently with the parameters.")
        params["horizon_path"] = str(repo)
    if "config_path" in signature.parameters:
        if not params.get("config_path") and params.get("run_id"):
            meta = service.get_run_meta(params["run_id"])["meta"]
            params["config_path"] = meta.get("config_path")
        if params.get("config_path"):
            params["config_path"] = str(repo_path(repo, params["config_path"]))

    signature.bind(**params)
    result = method(**params)
    return await result if inspect.isawaitable(result) else result


def error_result(exc: Exception) -> dict[str, Any]:
    """Avoid returning expanded config values or raw HTTP exception URLs."""
    cause = exc.__cause__ or exc
    if hasattr(cause, "errors"):
        errors = cause.errors(include_input=False, include_context=False, include_url=False)
        return {
            "code": "HZ_CONFIG_INVALID",
            "message": "Configuration validation failed.",
            "fields": [{"location": error["loc"], "type": error["type"]} for error in errors],
        }
    if hasattr(exc, "code"):
        return {"code": exc.code, "message": exc.message}
    if isinstance(exc, (ValueError, TypeError, FileNotFoundError, ModuleNotFoundError)):
        return {"code": type(exc).__name__, "message": str(exc)}
    return {
        "code": type(exc).__name__,
        "message": "Operation failed. Inspect run metadata and local diagnostics; redact credentials before sharing logs.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=OPERATIONS)
    parser.add_argument("--horizon-path", help="Checkout; defaults to HORIZON_PATH or discovery")
    parser.add_argument("--runs-root", help="Artifact directory; default: <checkout>/data/mcp-runs")
    parser.add_argument("--describe", action="store_true", help="Show the current service signature without executing")
    parameters = parser.add_mutually_exclusive_group()
    parameters.add_argument("--params", help="Native service parameters as a JSON object")
    parameters.add_argument("--params-file", help="Read parameters from a UTF-8 JSON file")
    args = parser.parse_args(argv)
    try:
        repo = find_checkout(args.horizon_path)
        with redirect_stdout(sys.stderr):
            data = asyncio.run(call_service(args, repo))
        result = {"ok": True, "operation": args.operation, "data": data}
    except Exception as exc:
        result = {"ok": False, "operation": args.operation, "error": error_result(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # Like MCP, successful dispatch does not imply business-level success.
    # Consumers must inspect missing_env, fetch_status, enrichment status, etc.
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
