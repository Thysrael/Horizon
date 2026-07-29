"""Authenticated configuration and backup API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..configuration import (
    BackupError,
    ConfigApplicationService,
    ConfigDocumentError,
    ConfigPatchError,
    ConfigServiceError,
    ConfigValidationFailed,
    ConfigWarningsNotAcknowledged,
    RevisionConflictError,
    apply_json_patch,
    build_redacted_diff,
    serialize_raw_config,
)
from ..models import Config
from .contracts import CandidateRequest, PatchRequest, RestoreRequest
from .initialization import example_config, minimal_config
from .security import error_response
from .ui_metadata import UI_METADATA


router = APIRouter(prefix="/api/v1")


def _dump(value: Any) -> Any:
    """Convert Pydantic responses to JSON-compatible values."""

    return value.model_dump(mode="json") if hasattr(value, "model_dump") else value


def _service(request: Request) -> ConfigApplicationService:
    return request.app.state.config_service


def _failure(request: Request, error: Exception) -> JSONResponse:
    """Map application failures to stable responses without rejected values."""

    if isinstance(error, RevisionConflictError):
        status_code = 409
    elif isinstance(
        error,
        (
            ConfigDocumentError,
            ConfigPatchError,
            ConfigValidationFailed,
            ConfigWarningsNotAcknowledged,
        ),
    ):
        status_code = 422
    elif isinstance(error, BackupError):
        status_code = 404 if error.code == "backup_not_found" else 422
    elif isinstance(error, FileNotFoundError):
        status_code = 404
    else:
        status_code = 500

    if isinstance(
        error,
        (ConfigServiceError, ConfigDocumentError, ConfigPatchError, BackupError),
    ):
        code = error.code
        message = error.message
    elif status_code == 404:
        code = "not_found"
        message = "The requested editor resource was not found."
    else:
        code = "configuration_io_error"
        message = "The configuration operation failed."

    if isinstance(error, (ConfigValidationFailed, ConfigWarningsNotAcknowledged)):
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": request.state.request_id,
                    "report": _dump(error.report),
                }
            },
        )
    return error_response(
        status_code,
        code,
        message,
        request.state.request_id,
    )


def _draft_from_patch(
    service: ConfigApplicationService,
    operations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a JSON-object draft for initial creation without persisting it."""

    candidate = apply_json_patch({}, operations)
    if not isinstance(candidate, dict):
        raise ConfigDocumentError(
            "invalid_root",
            "The configuration root must be a JSON object.",
        )
    serialize_raw_config(candidate)
    return candidate


def _save_body(result: Any) -> dict[str, Any]:
    body = _dump(result)
    body["validation"] = body.pop("report")
    return body


@router.get("/config")
async def get_config(request: Request) -> JSONResponse:
    service = _service(request)
    try:
        document = service.load()
        report = service.validate(document.data).report
        modified_at = datetime.fromtimestamp(
            service.config_path.stat().st_mtime,
            tz=timezone.utc,
        ).isoformat()
    except FileNotFoundError:
        return JSONResponse(
            {
                "config": None,
                "exists": False,
                "path": str(service.config_path),
                "revision": None,
                "modified_at": None,
                "validation": None,
                "summary": {
                    "valid": False,
                    "errors": 0,
                    "warnings": 0,
                    "missing_env": [],
                },
            }
        )
    except Exception as error:
        return _failure(request, error)

    return JSONResponse(
        {
            "config": document.data,
            "exists": True,
            "path": str(service.config_path),
            "revision": document.revision,
            "modified_at": modified_at,
            "validation": _dump(report),
            "summary": {
                "valid": report.valid,
                "errors": len(report.errors),
                "warnings": len(report.warnings),
                "missing_env": report.missing_env,
            },
        }
    )


@router.get("/schema")
async def get_schema(request: Request) -> dict[str, Any]:
    service = _service(request)
    example = example_config(Path(service.config_path))
    initialization = {"minimal": minimal_config()}
    if example is not None:
        initialization["example"] = example
    return {
        "schema": Config.model_json_schema(),
        "ui": UI_METADATA,
        "initialization": initialization,
    }


@router.post("/config/validate")
async def validate_config(
    payload: CandidateRequest,
    request: Request,
) -> JSONResponse:
    try:
        report = _service(request).validate(payload.config).report
        return JSONResponse({"validation": _dump(report)})
    except Exception as error:
        return _failure(request, error)


@router.post("/config/diff")
async def preview_config(
    payload: PatchRequest,
    request: Request,
) -> JSONResponse:
    service = _service(request)
    try:
        if not service.config_path.exists():
            if payload.revision is not None:
                raise RevisionConflictError(payload.revision, None)
            candidate = _draft_from_patch(service, payload.patch)
            report = service.validate(candidate).report
            diff = build_redacted_diff({}, candidate)
            return JSONResponse(
                {
                    "revision": None,
                    "validation": _dump(report),
                    "diff": _dump(diff),
                    "changed": diff.changed,
                }
            )

        if payload.revision is None:
            raise RevisionConflictError(None, service.load().revision)
        preview = service.preview(
            payload.patch,
            expected_revision=payload.revision,
        )
        return JSONResponse(
            {
                "revision": preview.revision,
                "validation": _dump(preview.report),
                "diff": _dump(preview.diff),
                "changed": preview.diff.changed,
            }
        )
    except Exception as error:
        return _failure(request, error)


@router.patch("/config")
async def save_config(
    payload: PatchRequest,
    request: Request,
) -> JSONResponse:
    service = _service(request)
    try:
        if service.config_path.exists():
            if payload.revision is None:
                raise RevisionConflictError(None, service.load().revision)
            result = service.save(
                payload.patch,
                expected_revision=payload.revision,
                acknowledge_warnings=payload.acknowledge_warnings,
            )
        else:
            if payload.revision is not None:
                raise RevisionConflictError(payload.revision, None)
            result = service.create(
                _draft_from_patch(service, payload.patch),
                acknowledge_warnings=payload.acknowledge_warnings,
            )
        return JSONResponse(_save_body(result))
    except Exception as error:
        return _failure(request, error)


@router.get("/backups")
async def list_backups(request: Request) -> JSONResponse:
    try:
        backups = [_dump(item) for item in _service(request).list_backups()]
        return JSONResponse({"backups": backups})
    except Exception as error:
        return _failure(request, error)


@router.get("/backups/{backup_id}/diff")
async def backup_diff(backup_id: str, request: Request) -> JSONResponse:
    service = _service(request)
    try:
        current = service.load()
        backup = service.backups.load(backup_id)
        diff = build_redacted_diff(current.data, backup.data)
        return JSONResponse(
            {
                "backup_id": backup_id,
                "diff": _dump(diff),
                "changed": diff.changed,
            }
        )
    except Exception as error:
        return _failure(request, error)


@router.post("/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    payload: RestoreRequest,
    request: Request,
) -> JSONResponse:
    if not payload.confirm:
        return error_response(
            422,
            "restore_not_confirmed",
            "Backup restore requires explicit confirmation.",
            request.state.request_id,
        )

    try:
        result = _service(request).restore(
            backup_id,
            expected_revision=payload.revision,
            acknowledge_warnings=payload.acknowledge_warnings,
        )
        return JSONResponse(_save_body(result))
    except Exception as error:
        return _failure(request, error)
