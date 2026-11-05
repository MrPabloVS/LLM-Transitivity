"""Define models and execution policy without evaluation-framework dependencies."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    identifier: str
    provider: str
    generation_group: str
    supports_reasoning: bool


@dataclass(frozen=True)
class GenerationPolicy:
    max_output_tokens: int = 1024
    max_connections: int = 2
    max_tasks: int = 1
    max_samples: int = 2
    request_timeout_seconds: int = 60
    request_max_retries: int = 2
    sdk_max_retries: int = 0
    flow_retry_attempts: int = 1
    flow_retry_cleanup: bool = False
    cache_prompt: bool = False
    stream: bool = False
    provider_fallback: bool = False
    require_parameters: bool = True
    reasoning_enabled: bool = False

    @property
    def maximum_planned_attempts(self) -> int:
        return (
            (self.request_max_retries + 1)
            * (self.sdk_max_retries + 1)
            * self.flow_retry_attempts
        )

    def metadata(self) -> dict:
        """Keep the existing generation-policy metadata names."""
        return {
            "max_output_tokens": self.max_output_tokens,
            "reasoning": "enabled where supported"
            if self.reasoning_enabled
            else "disabled where supported",
            "provider_fallback": self.provider_fallback,
            "cache_prompt": self.cache_prompt,
            "temperature": "provider default; omitted",
            "top_p": "provider default; omitted",
            "seed": "omitted; outputs are not deterministic",
            "request_timeout_seconds": self.request_timeout_seconds,
            "request_max_retries": self.request_max_retries,
            "sdk_max_retries": self.sdk_max_retries,
            "max_tasks": self.max_tasks,
            "max_samples": self.max_samples,
        }


MODEL_SPECS = (
    ModelSpec("openai/gpt-4o-mini", "openai", "earlier", False),
    ModelSpec("openai/gpt-6-luna", "openai", "later", True),
    ModelSpec("anthropic/claude-sonnet-4.5", "anthropic", "earlier", True),
    ModelSpec("anthropic/claude-sonnet-5", "anthropic", "later", True),
    ModelSpec("google/gemini-2.5-flash-lite", "google-ai-studio", "earlier", True),
    ModelSpec("google/gemini-3.1-flash-lite", "google-ai-studio", "later", True),
)
GENERATION_POLICY = GenerationPolicy()
