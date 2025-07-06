# limiter.py

from config import Config
import time
from collections import deque
import asyncio

_global_gemini_limiter = None
_limiter_lock = asyncio.Lock()

async def get_global_gemini_limiter():
    global _global_gemini_limiter
    
    if _global_gemini_limiter is not None:
        return _global_gemini_limiter

    async with _limiter_lock:
        if _global_gemini_limiter is None:
            _global_gemini_limiter = SlidingWindowLimiter(
                Config.rate_limit, Config.rate_limit_window
            )
    return _global_gemini_limiter

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