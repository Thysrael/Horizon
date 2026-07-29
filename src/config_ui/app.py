"""FastAPI application factory for the local configuration editor shell."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..configuration import ConfigApplicationService
from .api import router as config_router
from .security import (
    SESSION_COOKIE_NAME,
    LocalSecurityMiddleware,
    SessionStore,
    error_response,
)


PACKAGE_DIR = Path(__file__).resolve().parent


class BootstrapRequest(BaseModel):
    """One-time startup credential sent only in the request body."""

    token: str = Field(min_length=1, max_length=512)


def create_app(
    config_path: str | Path = "data/config.json",
    *,
    session_store: SessionStore | None = None,
) -> FastAPI:
    """Build an editor app without reading or exposing configuration data."""

    sessions = session_store or SessionStore()
    app = FastAPI(
        title="Horizon Config",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.config_service = ConfigApplicationService(config_path)
    app.state.session_store = sessions

    templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
    app.mount(
        "/static",
        StaticFiles(directory=PACKAGE_DIR / "static"),
        name="static",
    )
    app.add_middleware(LocalSecurityMiddleware, session_store=sessions)
    app.include_router(config_router)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        _error: RequestValidationError,
    ) -> JSONResponse:
        return error_response(
            422,
            "invalid_request",
            "The request body is invalid.",
            request.state.request_id,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request,
        error: StarletteHTTPException,
    ) -> JSONResponse:
        if error.status_code == 404:
            code = "not_found"
            message = "The requested local editor resource was not found."
        elif error.status_code == 405:
            code = "method_not_allowed"
            message = "That method is not allowed for this local editor resource."
        else:
            code = "request_failed"
            message = "The local editor rejected the request."
        return error_response(
            error.status_code,
            code,
            message,
            request.state.request_id,
        )

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={},
        )

    @app.post("/api/v1/session/bootstrap")
    async def bootstrap(
        request: Request,
        payload: BootstrapRequest,
    ) -> JSONResponse:
        session = sessions.consume_bootstrap(payload.token)
        if session is None:
            return error_response(
                401,
                "invalid_bootstrap",
                "The startup link is invalid or has already been used.",
                request.state.request_id,
            )

        response = JSONResponse(
            {
                "authenticated": True,
                "csrf_token": session.csrf_token,
            }
        )
        response.set_cookie(
            SESSION_COOKIE_NAME,
            session.session_id,
            httponly=True,
            samesite="strict",
            path="/",
        )
        return response

    @app.get("/api/v1/session")
    async def session_status(request: Request) -> dict[str, str | bool]:
        session = request.state.session
        return {
            "authenticated": True,
            "csrf_token": session.csrf_token,
        }

    return app
