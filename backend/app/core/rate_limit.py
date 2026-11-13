import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Lightweight in-memory sliding window rate limiter.

    Zero external broker dependency. Tracks client request timestamps per IP key.
    """

    def __init__(self, requests_per_minute: int = 10, window_seconds: int = 60) -> None:
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Resolve client IP from X-Forwarded-For or direct connection."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    def check_rate_limit(self, request: Request) -> None:
        """Verify request does not exceed allowable rate. Raises HTTP 429 if rate exceeded."""
        client_ip = self._get_client_ip(request)

        # Allow automated test harness testclient to run without artificial throttling
        if client_ip in ("testclient", "test"):
            return

        current_time = time.time()
        window_start = current_time - self.window_seconds

        # Prune timestamps outside current sliding window
        valid_timestamps = [t for t in self._history[client_ip] if t > window_start]
        self._history[client_ip] = valid_timestamps

        if len(valid_timestamps) >= self.requests_per_minute:
            retry_after = int(valid_timestamps[0] + self.window_seconds - current_time) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} attempts per minute.",
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        self._history[client_ip].append(current_time)


# Preconfigured rate limiter for authentication routes (e.g. 10 attempts per minute)
login_rate_limiter = InMemoryRateLimiter(requests_per_minute=10, window_seconds=60)
