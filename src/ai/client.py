"""AI client abstraction supporting multiple providers."""

import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from openai import AsyncAzureOpenAI, AsyncOpenAI, APIStatusError as OpenAIStatusError
from anthropic import AsyncAnthropic, BadRequestError as AnthropicBadRequestError
from google import genai
from google.genai import types


import logging

from ..models import AIConfig, AIProvider, AI_PROVIDER_DEFAULTS
from .tokens import record_usage
from .errors import AIProviderUnavailableError

logger = logging.getLogger(__name__)


_ENV_VAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SECRET_PREFIXES = (
    "sk-",
    "sk_",
    "AIza",
    "xai-",
    "gsk_",
    "hf_",
)
_DEFAULT_API_KEY_ENVS = {
    AIProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
    AIProvider.OPENAI: "OPENAI_API_KEY",
    AIProvider.AZURE: "AZURE_OPENAI_API_KEY",
    AIProvider.ALI: "DASHSCOPE_API_KEY",
    AIProvider.GEMINI: "GOOGLE_API_KEY",
    AIProvider.DOUBAO: "DOUBAO_API_KEY",
    AIProvider.MINIMAX: "MINIMAX_API_KEY",
    AIProvider.DEEPSEEK: "DEEPSEEK_API_KEY",
}


def _resolve_api_key(config: AIConfig, *, fallback: Optional[str] = None) -> str:
    api_key = os.getenv(config.api_key_env)
    if api_key:
        return api_key
    if fallback is not None:
        return fallback
    raise ValueError(_missing_api_key_message(config))


def _missing_api_key_message(config: AIConfig) -> str:
    expected_env = _DEFAULT_API_KEY_ENVS.get(config.provider)
    if expected_env:
        setup_hint = (
            f"Set {expected_env}=your_api_key in .env or your shell, then set "
            f'ai.api_key_env to "{expected_env}" in data/config.json.'
        )
    else:
        setup_hint = (
            "Set the provider API key in .env or your shell, then set "
            "ai.api_key_env to that environment variable name in data/config.json."
        )

    if _looks_like_api_key_value(config.api_key_env):
        return (
            "Missing API key: ai.api_key_env must be an environment variable "
            f"name, not the API key value. {setup_hint}"
        )

    return (
        "Missing API key environment variable configured by ai.api_key_env. "
        "ai.api_key_env should contain the environment variable name, not the "
        f"key value. {setup_hint}"
    )


def _looks_like_api_key_value(value: str) -> bool:
    if value.startswith(_SECRET_PREFIXES):
        return True
    return not bool(_ENV_VAR_RE.fullmatch(value))


def _normalize_ollama_base_url(base_url: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if "://" not in normalized:
        normalized = f"http://{normalized}"
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


def _is_temperature_unsupported(message: str) -> bool:
    lowered = message.lower()
    return "temperature" in lowered and (
        "deprecated" in lowered
        or "not support" in lowered
        or "unsupported" in lowered
        or "only the default" in lowered
        or "may only be set to 1" in lowered
        or "only 1 is allowed" in lowered
    )


def _is_token_limit_unsupported(message: str, use_max_completion_tokens: bool) -> bool:
    """Only switch token-limit parameters when the sent parameter is rejected."""
    lowered = message.lower()
    token_param = "max_completion_tokens" if use_max_completion_tokens else "max_tokens"
    return token_param in lowered and any(
        marker in lowered for marker in ("unsupported", "not support", "unknown parameter")
    )


def _chat_extra_body(extra_body: dict, include_temperature: bool, use_max_completion_tokens: bool) -> dict:
    """Preserve overrides without reintroducing rejected request parameters."""
    body = dict(extra_body)
    if not include_temperature:
        body.pop("temperature", None)
    token_param = "max_completion_tokens" if use_max_completion_tokens else "max_tokens"
    other_token_param = "max_tokens" if use_max_completion_tokens else "max_completion_tokens"
    if other_token_param in body:
        body.setdefault(token_param, body.pop(other_token_param))
    return body


class AIClient(ABC):
    """Abstract base class for AI clients."""

    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate completion from AI model.

        Args:
            system: System prompt
            user: User prompt
            temperature: Optional sampling temperature override
            max_tokens: Optional maximum tokens override

        Returns:
            str: Generated completion text
        """
        pass


class AnthropicClient(AIClient):
    """Client for Anthropic-compatible models."""

    def __init__(self, config: AIConfig):
        """Initialize Anthropic client.

        Args:
            config: AI configuration
        """
        self.config = config

        api_key = _resolve_api_key(config)

        kwargs = {"api_key": api_key}
        if config.base_url:
            kwargs["base_url"] = config.base_url

        self.client = AsyncAnthropic(**kwargs)
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self._supports_temperature = True

    async def complete(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate completion using Claude.

        Args:
            system: System prompt
            user: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            str: Generated text
        """
        temperature = self.temperature if temperature is None else temperature
        max_tokens = self.max_tokens if max_tokens is None else max_tokens

        # SDK 1.x removed the temperature keyword; extra_body also works with
        # older SDKs and Anthropic-compatible endpoints that still support it.
        extra_body = {"temperature": temperature, **(self.config.extra_body or {})}
        if not self._supports_temperature:
            extra_body.pop("temperature", None)
        request_kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "extra_body": extra_body,
        }
        try:
            message = await self.client.messages.create(**request_kwargs)
        except AnthropicBadRequestError as exc:
            if "temperature" not in extra_body or not _is_temperature_unsupported(str(exc)):
                raise
            self._supports_temperature = False
            extra_body.pop("temperature")
            message = await self.client.messages.create(**request_kwargs)
        usage = getattr(message, "usage", None)
        if usage is not None:
            record_usage(
                self.config.provider.value,
                input_tokens=getattr(usage, "input_tokens", 0),
                output_tokens=getattr(usage, "output_tokens", 0),
            )
        # Thinking blocks (e.g. enabled via ai.extra_body) precede the answer text.
        return "".join(block.text for block in message.content if block.type == "text")


class OpenAIClient(AIClient):
    """Client for OpenAI-compatible APIs."""

    _BASE_URL_ENVS = {
        "ollama": (
            "HORIZON_OLLAMA_BASE_URL",
            "OLLAMA_BASE_URL",
            "OLLAMA_HOST",
        ),
    }

    # Providers that don't support response_format
    _NO_RESPONSE_FORMAT = {"minimax"}

    # Providers that need temperature clamped to (0, 1]
    _TEMP_CLAMP = {"minimax"}

    # Newer reasoning-series / GPT-5 family models reject legacy `max_tokens`
    # and require `max_completion_tokens` instead.
    _MODELS_REQUIRING_MAX_COMPLETION_TOKENS = ("o1", "o3", "o4", "gpt-5")

    def __init__(self, config: AIConfig):
        """Initialize OpenAI-compatible client.

        Args:
            config: AI configuration
        """
        self.config = config

        fallback = "no_key" if config.provider == AIProvider.OLLAMA else None
        api_key = _resolve_api_key(config, fallback=fallback)

        kwargs = {"api_key": api_key}
        base_url = self._resolve_base_url(config)
        if base_url:
            kwargs["base_url"] = base_url

        self.client = AsyncOpenAI(**kwargs)
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.provider = config.provider.value
        # Some newer models (e.g. Claude Opus 4.7 on Bedrock Converse) reject
        # `temperature`. We learn this on first 400 and stop sending it.
        self._supports_temperature = True
        self._use_max_completion_tokens = any(
            config.model.startswith(prefix)
            for prefix in self._MODELS_REQUIRING_MAX_COMPLETION_TOKENS
        )

    @classmethod
    def _resolve_base_url(cls, config: AIConfig) -> Optional[str]:
        base_url = (config.base_url or "").strip()
        if not base_url:
            for env_name in cls._BASE_URL_ENVS.get(config.provider.value, ()):
                base_url = os.getenv(env_name, "").strip()
                if base_url:
                    break
        if not base_url:
            base_url = AI_PROVIDER_DEFAULTS.get(config.provider, {}).get("base_url") or ""

        if config.provider == AIProvider.OLLAMA and base_url:
            return _normalize_ollama_base_url(base_url)
        return base_url or None

    async def complete(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate completion using OpenAI-compatible API.

        Args:
            system: System prompt
            user: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            str: Generated text
        """
        temperature = self.temperature if temperature is None else temperature
        max_tokens = self.max_tokens if max_tokens is None else max_tokens

        # Clamp temperature for providers that require it
        if self.provider in self._TEMP_CLAMP and temperature <= 0:
            temperature = 0.01

        # Deployment aliases can hide both requirements; learn each at most once.
        retried_tokens = False
        while True:
            include_temperature = self._supports_temperature
            use_max_completion_tokens = self._use_max_completion_tokens
            try:
                response = await self._do_request(
                    system=system,
                    user=user,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    include_temperature=include_temperature,
                    use_max_completion_tokens=use_max_completion_tokens,
                )
                break
            except OpenAIStatusError as exc:
                if exc.status_code not in (400, 422):
                    raise
                if include_temperature and _is_temperature_unsupported(str(exc)):
                    self._supports_temperature = False
                    continue
                if retried_tokens or not _is_token_limit_unsupported(str(exc), use_max_completion_tokens):
                    raise
                self._use_max_completion_tokens = not use_max_completion_tokens
                retried_tokens = True
        usage = getattr(response, "usage", None)
        if usage is not None:
            record_usage(
                self.provider,
                input_tokens=getattr(usage, "prompt_tokens", 0),
                output_tokens=getattr(usage, "completion_tokens", 0),
            )
        return response.choices[0].message.content

    async def _do_request(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        include_temperature: bool,
        use_max_completion_tokens: bool,
    ):
        request_kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        token_param = "max_completion_tokens" if use_max_completion_tokens else "max_tokens"
        request_kwargs[token_param] = max_tokens
        if include_temperature:
            request_kwargs["temperature"] = temperature
        if self.provider not in self._NO_RESPONSE_FORMAT:
            request_kwargs["response_format"] = {"type": "json_object"}
        if self.config.extra_body:
            request_kwargs["extra_body"] = _chat_extra_body(
                self.config.extra_body, include_temperature, use_max_completion_tokens,
            )
        return await self.client.chat.completions.create(**request_kwargs)


class AzureOpenAIClient(AIClient):
    """Client for Azure OpenAI deployments.

    Uses the native AsyncAzureOpenAI client, which requires the deployment
    name (passed as `model`), azure_endpoint (resource base URL), and
    api_version. The deployment path is assembled internally by the SDK.
    """

    # Newer reasoning-series models reject legacy `max_tokens` and require
    # `max_completion_tokens` instead. Azure uses deployment names as `model`,
    # so a best-effort guess can be wrong for custom deployment aliases.
    _MODELS_REQUIRING_MAX_COMPLETION_TOKENS = ("o1", "o3", "o4", "gpt-5")

    def __init__(self, config: AIConfig):
        """Initialize Azure OpenAI client.

        Args:
            config: AI configuration
        """
        self.config = config

        api_key = _resolve_api_key(config)
        if not config.azure_endpoint_env:
            raise ValueError("azure_endpoint_env is required for azure provider")
        azure_endpoint = os.getenv(config.azure_endpoint_env)
        if not azure_endpoint:
            raise ValueError(f"Missing Azure endpoint: {config.azure_endpoint_env}")
        if not config.api_version:
            raise ValueError("api_version is required for azure provider")

        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=config.api_version,
        )
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self._supports_temperature = True
        self._use_max_completion_tokens = any(
            config.model.startswith(prefix)
            for prefix in self._MODELS_REQUIRING_MAX_COMPLETION_TOKENS
        )

    async def complete(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate completion using Azure OpenAI.

        Args:
            system: System prompt
            user: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            str: Generated text
        """
        temperature = self.temperature if temperature is None else temperature
        max_tokens = self.max_tokens if max_tokens is None else max_tokens

        # Each parameter can adapt once: at most three requests, in either order.
        retried_tokens = False
        while True:
            include_temperature = self._supports_temperature
            use_max_completion_tokens = self._use_max_completion_tokens
            try:
                response = await self._create_completion(
                    system=system,
                    user=user,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    include_temperature=include_temperature,
                    use_max_completion_tokens=use_max_completion_tokens,
                )
                break
            except OpenAIStatusError as exc:
                if exc.status_code not in (400, 422):
                    raise
                if include_temperature and _is_temperature_unsupported(str(exc)):
                    self._supports_temperature = False
                    continue
                if retried_tokens or not _is_token_limit_unsupported(str(exc), use_max_completion_tokens):
                    raise
                self._use_max_completion_tokens = not use_max_completion_tokens
                retried_tokens = True

        usage = getattr(response, "usage", None)
        if usage is not None:
            record_usage(
                "openai",
                input_tokens=getattr(usage, "prompt_tokens", 0),
                output_tokens=getattr(usage, "completion_tokens", 0),
            )
        return response.choices[0].message.content

    async def _create_completion(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        include_temperature: bool,
        use_max_completion_tokens: bool,
    ):
        tokens_kwarg = (
            {"max_completion_tokens": max_tokens}
            if use_max_completion_tokens
            else {"max_tokens": max_tokens}
        )
        extra_kwargs = {}
        if include_temperature:
            extra_kwargs["temperature"] = temperature
        if self.config.extra_body:
            extra_kwargs["extra_body"] = _chat_extra_body(
                self.config.extra_body, include_temperature, use_max_completion_tokens,
            )
        return await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            **tokens_kwarg,
            **extra_kwargs,
        )


class GeminiClient(AIClient):
    """Client for Google Gemini models."""

    def __init__(self, config: AIConfig):
        """Initialize Gemini client.

        Args:
            config: AI configuration
        """
        self.config = config
        if config.extra_body:
            raise ValueError("ai.extra_body is not supported for the gemini provider")

        api_key = _resolve_api_key(config)

        self.client = genai.Client(api_key=api_key)
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens

    async def complete(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate completion using Gemini.

        Args:
            system: System prompt
            user: User prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            str: Generated text
        """
        temperature = self.temperature if temperature is None else temperature
        max_tokens = self.max_tokens if max_tokens is None else max_tokens

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json"
            )
        )
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            total = getattr(usage, "total_token_count", 0) or 0
            prompt = getattr(usage, "prompt_token_count", 0) or 0
            completion = max(0, total - prompt)
            record_usage("gemini", input_tokens=prompt, output_tokens=completion)
        return response.text


def _uses_anthropic_compatible_api(config: AIConfig) -> bool:
    """Return whether MiniMax is configured for its Anthropic-compatible API."""
    base_url = (config.base_url or "").rstrip("/")
    return config.provider == AIProvider.MINIMAX and base_url.endswith("/anthropic")


def _create_single_client(config: AIConfig) -> AIClient:
    """Create a single AI client instance."""
    if config.provider == AIProvider.OPENAI_CHATGPT:
        from .chatgpt import ChatGPTClient
        return ChatGPTClient(config)
    if (
        config.provider == AIProvider.ANTHROPIC
        or _uses_anthropic_compatible_api(config)
    ):
        return AnthropicClient(config)
    elif config.provider == AIProvider.AZURE:
        return AzureOpenAIClient(config)
    elif config.provider == AIProvider.GEMINI:
        return GeminiClient(config)
    elif config.provider in {
        AIProvider.OPENAI,
        AIProvider.ALI,
        AIProvider.DOUBAO,
        AIProvider.MINIMAX,
        AIProvider.DEEPSEEK,
        AIProvider.OLLAMA,
    }:
        return OpenAIClient(config)
    else:
        raise ValueError(f"Unsupported AI provider: {config.provider}")


class ChainedAIClient(AIClient):
    """Chain multiple AI clients with automatic fallback.

    When a provider fails with a retryable error (rate limit, auth/quota,
    service unavailable, or empty response), automatically falls back to
    the next provider in the chain.

    Clients are created lazily so that missing API keys for downstream
    providers do not block startup when the primary provider works.
    """

    def __init__(
        self,
        configs: List[AIConfig],
        clients: Optional[List[AIClient]] = None,
        client_factory: Optional[Any] = None,
    ):
        self.configs = configs
        self._client_factory = client_factory or _create_single_client
        self._client_cache: Dict[int, AIClient] = {}
        # Allow tests to inject pre-built clients directly
        if clients is not None:
            for idx, client in enumerate(clients):
                self._client_cache[idx] = client

    def _get_client(self, index: int) -> AIClient:
        if index not in self._client_cache:
            self._client_cache[index] = self._client_factory(self.configs[index])
        return self._client_cache[index]

    async def complete(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        last_error: Optional[Exception] = None
        for i in range(len(self.configs)):
            try:
                client = self._get_client(i)
                result = await client.complete(system, user, temperature, max_tokens)
                if not result or not result.strip():
                    raise ValueError("Empty response from provider")
                return result
            except Exception as exc:
                if not self._should_fallback(exc):
                    raise
                last_error = exc
                if i < len(self.configs) - 1:
                    logger.warning(
                        "Provider %s failed (%s), falling back to %s...",
                        self.configs[i].provider.value, exc, self.configs[i + 1].provider.value,
                    )
        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    @staticmethod
    def _should_fallback(exc: Exception) -> bool:
        """Determine if an error warrants fallback to the next provider."""
        if isinstance(exc, AIProviderUnavailableError):
            return False
        msg = str(exc).lower()
        if "429" in msg or "rate limit" in msg:
            return True
        if "401" in msg or "403" in msg or "quota" in msg or "exceeded" in msg:
            return True
        if "502" in msg or "503" in msg or "service unavailable" in msg:
            return True
        if "empty response" in msg:
            return True
        return False


def _create_chained_client(config: AIConfig) -> ChainedAIClient:
    """Build a ChainedAIClient from a comma-separated provider chain."""
    provider_chain = config.provider_chain or ""
    provider_names = [p.strip() for p in provider_chain.split(",") if p.strip()]
    if not provider_names:
        raise ValueError("provider_chain is empty")

    chain_configs: List[AIConfig] = []
    for name in provider_names:
        try:
            provider = AIProvider(name)
        except ValueError:
            raise ValueError(f"Unsupported AI provider in chain: {name}")

        defaults = AI_PROVIDER_DEFAULTS.get(provider, {})
        base_url = config.base_url if provider == config.provider else defaults.get("base_url")
        cfg = AIConfig(
            provider=provider,
            model=(
                config.model
                if provider == config.provider and provider in {AIProvider.MINIMAX, AIProvider.OPENAI_CHATGPT}
                else defaults.get("model", config.model)
            ),
            api_key_env=defaults.get("api_key_env", config.api_key_env),
            chatgpt_account=config.chatgpt_account if provider == AIProvider.OPENAI_CHATGPT else None,
            base_url=base_url,
            extra_body=config.extra_body if provider == config.provider else None,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            throttle_sec=config.throttle_sec,
            analysis_concurrency=config.analysis_concurrency,
            enrichment_concurrency=config.enrichment_concurrency,
            languages=config.languages,
            azure_endpoint_env=(
                config.azure_endpoint_env or defaults.get("azure_endpoint_env")
                if provider == AIProvider.AZURE
                else None
            ),
            api_version=(
                config.api_version or defaults.get("api_version")
                if provider == AIProvider.AZURE
                else None
            ),
        )
        chain_configs.append(cfg)

    return ChainedAIClient(chain_configs)


def create_ai_client(config: AIConfig) -> AIClient:
    """Factory function to create appropriate AI client.

    Args:
        config: AI configuration

    Returns:
        AIClient: Initialized AI client

    Raises:
        ValueError: If provider is not supported
    """
    if config.provider_chain:
        return _create_chained_client(config)
    return _create_single_client(config)
