import os
import time
import threading
from typing import Dict, Deque, Tuple, Optional
from collections import deque
from Multi_Agent_TourAI.utils import get_logger

logger = get_logger("Multi_Agent_TourAI.auth.rate_limiter")

# Default rate limits: (max_requests, window_seconds)
DEFAULT_LIMITS: Dict[str, Tuple[int, int]] = {
    "plan": (5, 60),            # 5 requests per minute for plan creation / streaming
    "resume": (10, 60),         # 10 requests per minute for resume / resume streaming
    "forgot_password": (5, 60), # 5 forgot password requests per minute
    "verify_otp": (10, 60),     # 10 OTP verification attempts per minute
    "reset_password": (5, 60),  # 5 password reset submissions per minute
    "resend_otp": (3, 60),      # 3 OTP resend requests per minute
}


class BaseRateLimiter:
    def is_rate_limited(self, key: str, endpoint_type: str = "plan") -> Tuple[bool, int]:
        """
        Returns (is_limited, retry_after_seconds).
        is_limited is True if limit is exceeded.
        """
        raise NotImplementedError


class InMemoryRateLimiter(BaseRateLimiter):
    """
    Thread-safe in-memory sliding-window rate limiter for local development.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._history: Dict[str, Deque[float]] = {}
        logger.info(
            "[RATE_LIMIT] Running in local-development mode (in-memory sliding window rate limiter). "
            "Configure REDIS_URL for production distributed rate limiting."
        )

    def is_rate_limited(self, key: str, endpoint_type: str = "plan") -> Tuple[bool, int]:
        max_requests, window = DEFAULT_LIMITS.get(endpoint_type, (10, 60))
        now = time.time()
        bucket_key = f"{endpoint_type}:{key}"

        with self._lock:
            if bucket_key not in self._history:
                self._history[bucket_key] = deque()

            q = self._history[bucket_key]
            # Evict timestamps outside the window
            while q and (now - q[0] > window):
                q.popleft()

            if len(q) >= max_requests:
                oldest = q[0]
                retry_after = max(1, int(window - (now - oldest)))
                logger.warning(
                    f"[RATE_LIMIT] Rate limit exceeded for {key} on {endpoint_type}. "
                    f"Count={len(q)}/{max_requests}. Retry after {retry_after}s"
                )
                return True, retry_after

            q.append(now)
            return False, 0


class RedisRateLimiter(BaseRateLimiter):
    """
    Production-grade distributed rate limiter backed by Redis using sliding window sorted sets.
    """
    def __init__(self, redis_client):
        self.redis = redis_client
        logger.info("[RATE_LIMIT] Initialized Redis-backed distributed rate limiter.")

    def is_rate_limited(self, key: str, endpoint_type: str = "plan") -> Tuple[bool, int]:
        max_requests, window = DEFAULT_LIMITS.get(endpoint_type, (10, 60))
        now = time.time()
        redis_key = f"tourai:ratelimit:{endpoint_type}:{key}"
        clear_before = now - window

        try:
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(redis_key, 0, clear_before)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {str(now): now})
            pipe.expire(redis_key, window + 5)
            results = pipe.execute()

            current_count = results[1]
            if current_count >= max_requests:
                # Limit exceeded; remove the entry we just optimistically added
                self.redis.zrem(redis_key, str(now))
                return True, window
            return False, 0
        except Exception as e:
            logger.error(f"[RATE_LIMIT] Redis failure, falling back to allow: {e}")
            return False, 0


_limiter_instance: Optional[BaseRateLimiter] = None


def get_rate_limiter() -> BaseRateLimiter:
    global _limiter_instance
    if _limiter_instance is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis
                client = redis.from_url(redis_url, socket_connect_timeout=1.0, socket_timeout=1.0)
                client.ping()
                _limiter_instance = RedisRateLimiter(client)
            except Exception as e:
                logger.warning(f"[RATE_LIMIT] Could not connect to Redis at {redis_url}: {e}. Falling back to in-memory.")
                _limiter_instance = InMemoryRateLimiter()
        else:
            _limiter_instance = InMemoryRateLimiter()
    return _limiter_instance

