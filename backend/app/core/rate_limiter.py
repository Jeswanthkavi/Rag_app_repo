import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status
from app.core.config import settings
from app.core.security_logger import log_security_event


class RateLimiter:
    """
    In-memory sliding-window rate limiter for protecting sensitive endpoints
    (auth, LLM chat synthesis, and document ingestion) against abuse and DoS.
    """

    def __init__(self):
        # Store rolling timestamps: { "ip:route": [t1, t2, ...] }
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._last_prune = time.time()

    def _prune(self, now: float, window_seconds: float = 60.0):
        # Prune stale records every 60 seconds
        if now - self._last_prune > 60.0:
            stale_threshold = now - window_seconds
            keys_to_delete = []
            for key, timestamps in self._requests.items():
                self._requests[key] = [t for t in timestamps if t > stale_threshold]
                if not self._requests[key]:
                    keys_to_delete.append(key)
            for k in keys_to_delete:
                del self._requests[k]
            self._last_prune = now

    def check_rate_limit(self, request: Request, endpoint_tag: str, max_requests: int, window_seconds: float = 60.0):
        now = time.time()
        self._prune(now, window_seconds)

        client_ip = request.client.host if request.client else "unknown"
        bucket_key = f"{client_ip}:{endpoint_tag}"

        # Filter timestamps in current sliding window
        window_start = now - window_seconds
        recent_timestamps = [t for t in self._requests[bucket_key] if t > window_start]
        self._requests[bucket_key] = recent_timestamps

        if len(recent_timestamps) >= max_requests:
            log_security_event(
                "RATE_LIMIT_EXCEEDED",
                client_ip=client_ip,
                detail=f"Rate limit triggered on {endpoint_tag}: {len(recent_timestamps)} requests in {window_seconds}s",
                severity="WARNING"
            )
            retry_after = int(window_seconds - (now - recent_timestamps[0])) if recent_timestamps else 60
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests to {endpoint_tag}. Rate limit exceeded. Please wait {max(1, retry_after)} seconds.",
                headers={"Retry-After": str(max(1, retry_after))},
            )

        self._requests[bucket_key].append(now)


rate_limiter = RateLimiter()

