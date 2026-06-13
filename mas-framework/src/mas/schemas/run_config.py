"""Pydantic models for run_config.yaml."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ResponseFormat(str, Enum):
    JSON = "json"
    TEXT = "text"
    STRUCTURED = "structured"


class RoutingRule(BaseModel):
    task: str
    model: str
    provider: str


class ProviderConfig(BaseModel):
    api_key_env: str | None = None
    base_url: str | None = None
    rate_limit_rpm: int | None = None


class RetryConfig(BaseModel):
    max_retries: int = Field(ge=0, default=3)
    backoff_base_seconds: float = 1.0
    backoff_max_seconds: float = 16.0
    backoff_jitter: float = 0.1


class RoutingConfig(BaseModel):
    enabled: bool = False
    rules: list[RoutingRule] = Field(default_factory=list)


class LLMConfig(BaseModel):
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    max_tokens_per_response: int = Field(ge=1, default=1024)
    response_format: ResponseFormat = ResponseFormat.JSON
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    retry: RetryConfig = Field(default_factory=RetryConfig)


class CostConfig(BaseModel):
    budget_total_usd: float = Field(ge=0, default=5.0)
    budget_per_repetition_usd: float | None = None
    alert_threshold_pct: int = Field(ge=0, le=100, default=80)
    abort_on_exceed: bool = True


class CacheConfig(BaseModel):
    enabled: bool = True
    backend: str = "sqlite"
    cache_path: str = ".cache/llm_responses.db"
    ttl_hours: int = 168


class OutputConfig(BaseModel):
    base_dir: str = "output/runs"
    include_raw_responses: bool = True
    include_prompt_snapshots: bool = True
    log_level: str = "INFO"


class RunConfig(BaseModel):
    """Top-level model for run_config.yaml."""

    id: str = "default"
    seed: int = 42
    repetitions: int = Field(ge=1, default=1)
    description: str = ""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    cost: CostConfig = Field(default_factory=CostConfig)
    caching: CacheConfig = Field(default_factory=CacheConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
