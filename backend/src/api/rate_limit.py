"""Rate limiting en memoria por IP (single-tenant, un proceso)."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

_buckets: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_rate_limit(request: Request, scope: str, limit_per_minute: int) -> None:
    """Lanza 429 si la IP supera limit_per_minute en ventana de 60 s."""
    if limit_per_minute <= 0:
        return
    key = f"{scope}:{_client_ip(request)}"
    now = time.monotonic()
    window = 60.0
    hits = [t for t in _buckets[key] if now - t < window]
    if len(hits) >= limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    hits.append(now)
    _buckets[key] = hits
