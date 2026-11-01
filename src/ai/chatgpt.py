"""Responses adapter for officially authorized ChatGPT plan usage."""

from __future__ import annotations

import asyncio

import httpx
from openai import APIConnectionError, APIError, AsyncOpenAI

from .chatgpt_auth import ChatGPTAuth, RESOURCE, api_error
from .client import AIClient
from .errors import AIProviderUnavailableError
from .tokens import record_usage
from ..models import AIConfig


class ChatGPTClient(AIClient):
    def __init__(self, config: AIConfig, *, auth: ChatGPTAuth | None = None):
        self.config = config
        self.auth = auth or ChatGPTAuth()
        # Pin the registration for this run, including across concurrent requests.
        session = self.auth.status(config.chatgpt_account)
        if not session["connected"]:
            raise AIProviderUnavailableError("ChatGPT is not connected. Run horizon-chatgpt login.")
        if not session["plan_usage"]:
            raise AIProviderUnavailableError("ChatGPT plan usage is not enabled. Run horizon-chatgpt login --enable-plan.")
        self.account = session["client_id"]
        self.client = AsyncOpenAI(
            api_key="managed-by-horizon", base_url=RESOURCE, max_retries=0,
            timeout=httpx.Timeout(120, connect=20),
        )
        self._blocked: AIProviderUnavailableError | None = None

    async def complete(
        self, system: str, user: str,
        temperature: float | None = None, max_tokens: int | None = None,
    ) -> str:
        # These common interface options are unsupported by the plan-usage preview.
        # Never forward them, extra_body, or a Chat Completions system message.
        if self._blocked is not None:
            raise self._blocked
        request_id = None
        try:
            token = await asyncio.to_thread(self.auth.access_token, self.account)
            if self._blocked is not None:
                raise self._blocked
            client = self.client.with_options(api_key=token)
            stream = await client.responses.create(
                model=self.config.model,
                instructions=system,
                input=[{"role": "user", "content": user}],
                store=False,
                stream=True,
            )
            request_id = stream.response.headers.get("x-request-id")
            async with stream:
                async for event in stream:
                    if event.type == "response.failed":
                        error = event.response.error
                        raise api_error({
                            "code": getattr(error, "code", None), "param": getattr(error, "param", None),
                        }, request_id=request_id)
                    elif event.type == "error":
                        raise api_error({
                            "code": getattr(event, "code", None), "param": getattr(event, "param", None),
                        }, request_id=request_id)
                    elif event.type == "response.incomplete":
                        raise RuntimeError("ChatGPT response was incomplete; partial output was discarded.")
                    elif event.type == "response.completed":
                        if event.response.status != "completed" or event.response.error is not None:
                            raise RuntimeError("Invalid ChatGPT terminal response; partial output was discarded.")
                        # Only the terminal response is authoritative, never partial deltas.
                        text = event.response.output_text
                        if not text.strip():
                            raise RuntimeError("Empty response from ChatGPT.")
                        usage = event.response.usage
                        if usage is not None:
                            record_usage(
                                "openai-chatgpt", input_tokens=usage.input_tokens,
                                output_tokens=usage.output_tokens,
                            )
                        return text
            raise RuntimeError("ChatGPT stream ended without response.completed; partial output was discarded.")
        except (APIConnectionError, httpx.HTTPError):
            raise RuntimeError("ChatGPT connection failed; partial output was discarded.") from None
        except APIError as exc:
            # The SDK raises APIError for SSE error objects as well as HTTP errors.
            error = api_error(
                exc.body, getattr(exc, "status_code", None), getattr(exc, "request_id", None) or request_id,
            )
            if isinstance(error, AIProviderUnavailableError):
                self._blocked = error
            raise error from None
        except AIProviderUnavailableError as exc:
            self._blocked = exc
            raise
