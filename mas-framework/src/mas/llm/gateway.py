"""Unified LLM Gateway using litellm for multi-provider support."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

import litellm
import structlog

from mas.schemas.run_config import LLMConfig

log = structlog.get_logger()

# Suppress litellm's verbose debug output
litellm.suppress_debug_info = True


@dataclass
class LLMResponse:
    """Normalized response from any LLM provider."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cached: bool = False


class LLMGateway:
    """Sends prompts to LLM providers via litellm."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._setup_api_keys()

    def _setup_api_keys(self) -> None:
        """Verify API keys are available in environment."""
        for provider_name, provider_cfg in self.config.providers.items():
            if provider_cfg.api_key_env:
                key = os.environ.get(provider_cfg.api_key_env)
                if not key:
                    log.warning(
                        "api_key_not_found",
                        provider=provider_name,
                        env_var=provider_cfg.api_key_env,
                    )

    async def send(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Send messages to LLM and return normalized response."""
        model = model or self.config.default_model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens_per_response

        start = time.perf_counter()

        # Resolve base_url and api_key from provider config
        api_base = None
        api_key = None
        provider_name = self.config.default_provider
        if provider_name in self.config.providers:
            provider_cfg = self.config.providers[provider_name]
            api_base = provider_cfg.base_url
            if provider_cfg.api_key_env:
                api_key = os.environ.get(provider_cfg.api_key_env)

        try:
            kwargs: dict = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if api_base:
                kwargs["api_base"] = api_base
            if api_key:
                kwargs["api_key"] = api_key
            if self.config.response_format.value == "json":
                kwargs["response_format"] = {"type": "json_object"}

            response = await litellm.acompletion(**kwargs)
        except Exception as e:
            log.error("llm_call_failed", model=model, error=str(e))
            raise

        latency_ms = (time.perf_counter() - start) * 1000

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model or model,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            latency_ms=round(latency_ms, 1),
        )
