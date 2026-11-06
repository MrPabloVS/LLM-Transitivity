"""Define models and execution policy without evaluation-framework dependencies."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    identifier: str
    provider: str
    generation_group: str
    supports_reasoning: bool
    service_tier: str
    reasoning_effort: str | None = None
    reasoning_enabled: bool | None = None


@dataclass(frozen=True)
class GenerationPolicy:
    max_output_tokens: int = 1024
    max_connections: int = 16
    max_tasks: int = 1
    max_samples: int = 16
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
    ModelSpec("openai/gpt-4o-mini", "openai", "earlier", False, "default"),
    ModelSpec("openai/gpt-6-luna", "openai/flex", "later", True, "flex"),
    ModelSpec("anthropic/claude-sonnet-4.5", "anthropic", "earlier", True, "default"),
    ModelSpec("anthropic/claude-sonnet-5", "anthropic", "later", True, "default"),
    ModelSpec(
        "google/gemini-2.5-flash-lite", "google-ai-studio/flex", "earlier", True, "flex"
    ),
    ModelSpec(
        "google/gemini-3.1-flash-lite", "google-ai-studio/flex", "later", True, "flex"
    ),
)
GENERATION_POLICY = GenerationPolicy()

HAIKU_SPECS = tuple(
    ModelSpec("anthropic/claude-haiku-4.5", "anthropic", "earlier", True, "default")
    if model.identifier == "anthropic/claude-sonnet-4.5"
    else ModelSpec(
        "anthropic/claude-haiku-5.5", "anthropic", "later", True, "default", "medium"
    )
    if model.identifier == "anthropic/claude-sonnet-5"
    else model
    for model in MODEL_SPECS
)


PILOT2_SPECS = (
    MODEL_SPECS[0],
    MODEL_SPECS[1],
    ModelSpec(
        "anthropic/claude-sonnet-4.6", "anthropic", "earlier", True, "default", "medium"
    ),
    ModelSpec(
        "anthropic/claude-sonnet-5.5",
        "anthropic",
        "later",
        True,
        "default",
        "low",
        True,
    ),
    ModelSpec(
        "google/gemini-3.1-flash-lite", "google-ai-studio/flex", "earlier", True, "flex"
    ),
    ModelSpec(
        "google/gemini-3.5-flash-lite",
        "google-ai-studio/flex",
        "later",
        True,
        "flex",
        "minimal",
        True,
    ),
)


def profile_models(
    profile: str = "sonnet", selected: tuple[str, ...] | None = None
) -> tuple[ModelSpec, ...]:
    """Select an explicit profile without changing the historical default."""
    profiles = {
        "sonnet": MODEL_SPECS,
        "haiku": HAIKU_SPECS,
        "pilot2": PILOT2_SPECS,
    }
    if profile not in profiles:
        raise ValueError(f"Unknown model profile: {profile}")
    models = profiles[profile]
    if selected is None:
        return models
    if (
        not selected
        or len(set(selected)) != len(selected)
        or not set(selected) <= {m.identifier for m in models}
    ):
        raise ValueError("Selected models must be unique members of the profile")
    return tuple(m for m in models if m.identifier in selected)
