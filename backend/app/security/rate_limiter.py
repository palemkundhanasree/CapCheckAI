import time
import threading
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from app.config import settings


class InMemoryRateLimiter:
    """Thread-safe sliding-window rate limiter per client IP."""
    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 20):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.window_seconds = 60
        self._records: Dict[str, list] = {}
        self._lock = threading.Lock()

    def check_rate_limit(self, client_ip: str) -> None:
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            if client_ip not in self._records:
                self._records[client_ip] = [now]
                return

            # Purge older timestamps
            timestamps = [t for t in self._records[client_ip] if t > cutoff]
            self._records[client_ip] = timestamps

            if len(timestamps) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute allowed."
                )

            self._records[client_ip].append(now)


rate_limiter = InMemoryRateLimiter(
    requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    burst_limit=settings.BURST_LIMIT
)


async def rate_limit_dependency(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    rate_limiter.check_rate_limit(client_ip)
