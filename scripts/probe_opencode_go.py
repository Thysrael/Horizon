#!/usr/bin/env python3
"""Probe OpenCode Go model compatibility for Horizon-style requests.

This script helps answer practical questions like:
- Which OpenCode Go models work on the OpenAI-compatible endpoint?
- Does a model accept `response_format={"type": "json_object"}`?
- Does it accept `temperature`?
- Does it require `max_tokens` or `max_completion_tokens`?

Usage examples:

  uv run python scripts/probe_opencode_go.py
  uv run python scripts/probe_opencode_go.py --models kimi-k2.6 glm-5.2
  uv run python scripts/probe_opencode_go.py --timeout 90 --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv


DEFAULT_BASE_URL = "https://opencode.ai/zen/go/v1"
DEFAULT_MODELS = [
    "kimi-k2.7-code",
    "kimi-k2.6",
    "glm-5.2",
    "glm-5.1",
    "deepseek-v4-pro",
    "deepseek-v4-flash",
    "mimo-v2.5",
    "mimo-v2.5-pro",
]


@dataclass
class ProbeCase:
    name: str
    use_temperature: bool
    use_response_format: bool
    token_param: str


CASES = [
    ProbeCase(
        name="horizon_default",
        use_temperature=True,
        use_response_format=True,
        token_param="max_tokens",
    ),
    ProbeCase(
        name="no_response_format",
        use_temperature=True,
        use_response_format=False,
        token_param="max_tokens",
    ),
    ProbeCase(
        name="no_temperature",
        use_temperature=False,
        use_response_format=True,
        token_param="max_tokens",
    ),
    ProbeCase(
        name="max_completion_tokens",
        use_temperature=True,
        use_response_format=True,
        token_param="max_completion_tokens",
    ),
    ProbeCase(
        name="minimal",
        use_temperature=False,
        use_response_format=False,
        token_param="max_tokens",
    ),
]


def build_payload(model: str, case: ProbeCase) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return only valid JSON."},
            {
                "role": "user",
                "content": (
                    'Return exactly this JSON object: '
                    '{"ok": true, "model": "' + model + '"}'
                ),
            },
        ],
        case.token_param: 80,
    }
    if case.use_temperature:
        payload["temperature"] = 0.3
    if case.use_response_format:
        payload["response_format"] = {"type": "json_object"}
    return payload


async def probe_case(
    client: httpx.AsyncClient,
    *,
    model: str,
    case: ProbeCase,
) -> dict[str, Any]:
    try:
        response = await client.post(
            "/chat/completions",
            json=build_payload(model, case),
        )
    except Exception as exc:  # network / timeout / transport
        return {
            "ok": False,
            "status": None,
            "case": case.name,
            "error": f"transport_error: {exc}",
        }

    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text[:500]}

    if response.is_success:
        choice = None
        if isinstance(body, dict):
            choices = body.get("choices")
            if isinstance(choices, list) and choices:
                choice = choices[0]
        message = (choice or {}).get("message", {}) if isinstance(choice, dict) else {}
        return {
            "ok": True,
            "status": response.status_code,
            "case": case.name,
            "content": message.get("content"),
            "reasoning": message.get("reasoning"),
            "finish_reason": (choice or {}).get("finish_reason") if isinstance(choice, dict) else None,
        }

    error = body.get("error") if isinstance(body, dict) else None
    return {
        "ok": False,
        "status": response.status_code,
        "case": case.name,
        "error": error if error is not None else body,
    }


async def probe_model(
    client: httpx.AsyncClient,
    model: str,
) -> dict[str, Any]:
    results = []
    for case in CASES:
        results.append(await probe_case(client, model=model, case=case))
    return {"model": model, "results": results}


def summarize(model_result: dict[str, Any]) -> str:
    parts = [model_result["model"]]
    for result in model_result["results"]:
        status = "OK" if result["ok"] else "FAIL"
        detail = result.get("finish_reason") or result.get("error")
        if isinstance(detail, dict):
            detail = detail.get("message") or json.dumps(detail, ensure_ascii=False)
        parts.append(f"  - {result['case']}: {status} ({detail})")
    return "\n".join(parts)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="*", default=DEFAULT_MODELS)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key-env", default="OPENCODE_API_KEY")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(
            f"Missing API key. Set {args.api_key_env} in .env or your shell first."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(
        base_url=args.base_url,
        headers=headers,
        timeout=httpx.Timeout(args.timeout),
    ) as client:
        results = []
        for model in args.models:
            results.append(await probe_model(client, model))

    if args.as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for result in results:
            print(summarize(result))
            print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
