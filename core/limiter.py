import time
from collections import deque

from core.enums import MODEL_TO_RATE_LIMIT_MAP, RateLimits

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
        return False
        

def create_limiter_pool() -> dict[str, SlidingWindowLimiter]:
    return {
        model_enum.value: SlidingWindowLimiter(
            max_requests=rate_limit_enum.value,
            window_size=RateLimits.RATE_LIMIT_WINDOW.value
        )
        for model_enum, rate_limit_enum in MODEL_TO_RATE_LIMIT_MAP.items()
    }