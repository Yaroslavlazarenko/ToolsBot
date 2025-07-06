import time
from collections import deque
import asyncio

from typing import Dict
from core.enums import GeminiModel, RateLimits

_limiter_pool: Dict[str, 'SlidingWindowLimiter'] | None = None
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
        

async def get_limiter_pool() -> Dict[str, SlidingWindowLimiter]:
    global _limiter_pool
    if _limiter_pool is not None:
        return _limiter_pool
    async with _pool_init_lock:
        if _limiter_pool is None:
            _limiter_pool = {
                GeminiModel.GEMINI_2_5_PRO: SlidingWindowLimiter(
                    max_requests=RateLimits.RATE_LIMIT_2_5_PRO.value, window_size=RateLimits.RATE_LIMIT_WINDOW.value
                ),
                GeminiModel.GEMINI_2_5_FLASH: SlidingWindowLimiter(
                    max_requests=RateLimits.RATE_LIMIT_2_5_FLASH.value, window_size=RateLimits.RATE_LIMIT_WINDOW.value
                ),
                GeminiModel.GEMINI_2_5_FLASH_LITE: SlidingWindowLimiter(
                    max_requests=RateLimits.RATE_LIMIT_2_5_FLASH_LITE.value, window_size=RateLimits.RATE_LIMIT_WINDOW.value
                ),
            }
    return _limiter_pool