import time
from collections import deque
import asyncio

from core.enums import MODEL_TO_RATE_LIMIT_MAP, RateLimits

_limiter_pool: dict[str, "SlidingWindowLimiter"] | None = None
_pool_init_lock = asyncio.Lock()


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_size: int):
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = deque()

    def allow_request(self) -> bool:
        current_time = time.time()

        while self.requests and self.requests[0] <= current_time - self.window_size:
            self.requests.popleft()

        if len(self.requests) < self.max_requests:
            self.requests.append(current_time)
            return True
        else:
            return False
        

async def get_limiter_pool() -> dict[str, SlidingWindowLimiter]:
    global _limiter_pool

    if _limiter_pool is not None:
        return _limiter_pool
    
    async with _pool_init_lock:
        if _limiter_pool is None:
            _limiter_pool = {
                model_enum.value: SlidingWindowLimiter(
                    max_requests=rate_limit_enum.value,
                    window_size=RateLimits.RATE_LIMIT_WINDOW.value
                )
                for model_enum, rate_limit_enum in MODEL_TO_RATE_LIMIT_MAP.items()
            }
    return _limiter_pool