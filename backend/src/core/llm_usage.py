"""Métricas de uso de tokens LLM."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UsageStats:
    """Acumulador mutable de tokens por tick del clasificador."""

    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_content_tokens: int = 0
    providers: list[str] = field(default_factory=list)

    def add(self, usage: dict[str, int], provider: str) -> None:
        if not usage:
            self.llm_calls += 1
            self.providers.append(provider)
            return
        self.llm_calls += 1
        self.prompt_tokens += int(usage.get("prompt_tokens", 0))
        self.completion_tokens += int(usage.get("completion_tokens", 0))
        self.total_tokens += int(usage.get("total_tokens", 0))
        self.cached_content_tokens += int(usage.get("cached_content_token_count", 0))
        self.providers.append(provider)

    def as_log_dict(self) -> dict:
        return {
            "llm_calls": self.llm_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cached_content_tokens": self.cached_content_tokens,
            "providers": self.providers,
        }


def merge_usage_stats(target: UsageStats | None, usage: dict[str, int], provider: str) -> None:
    if target is not None:
        target.add(usage, provider)
