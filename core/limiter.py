import time
from collections import deque
import asyncio
from typing import Dict
from contextlib import asynccontextmanager

# --- НАЧАЛО ИСПРАВЛЕНИЙ ---
from core.enums import GeminiModel, RateLimits
# --- КОНЕЦ ИСПРАВЛЕНИЙ ---

_limiter_pool: Dict[str, 'SlidingWindowLimiter'] | None = None
# --- НАЧАЛО ИСПРАВЛЕНИЙ ---
_pool_init_lock = asyncio.Lock()
# --- КОНЕЦ ИСПРАВЛЕНИЙ ---


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_size: int):
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = deque()
        self._lock = asyncio.Lock()

    async def allow_request(self) -> bool:
        async with self._lock:
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

class ConcurrencyLimiter:
    def __init__(self, max_concurrent_requests: int):
        if max_concurrent_requests <= 0:
            raise ValueError("Maximum concurrent requests must be positive.")
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)

    @asynccontextmanager
    async def request_slot(self):
        await self.semaphore.acquire()
        try:
            yield
        finally:
            self.semaphore.release()

async def get_concurrency_limiter_pool() -> Dict[str, ConcurrencyLimiter]:
    global _limiter_pool
    if _limiter_pool is not None:
        return _limiter_pool
    async with _pool_init_lock:
        if _limiter_pool is None:
            _limiter_pool = {
                GeminiModel.GEMINI_2_5_PRO: ConcurrencyLimiter(
                    max_concurrent_requests=RateLimits.RATE_LIMIT_2_5_PRO.value
                ),
                GeminiModel.GEMINI_2_5_FLASH: ConcurrencyLimiter(
                    max_concurrent_requests=RateLimits.RATE_LIMIT_2_5_FLASH.value
                ),
                GeminiModel.GEMINI_2_5_FLASH_LITE: ConcurrencyLimiter(
                    max_concurrent_requests=RateLimits.RATE_LIMIT_2_5_FLASH_LITE.value
                ),
            }
    return _limiter_pool

class DualLimiter:
    def __init__(self, max_concurrent: int, max_per_window: int, window_size: int):
        if max_concurrent <= 0 or max_per_window <= 0:
            raise ValueError("Limiter values must be positive.")
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.requests = deque()
        self.max_per_window = max_per_window
        self.window_size = window_size
        self._window_lock = asyncio.Lock()

    @asynccontextmanager
    async def request_slot(self):
        while True:
            async with self._window_lock:
                current_time = time.time()
                while self.requests and self.requests[0] <= current_time - self.window_size:
                    self.requests.popleft()
                if len(self.requests) < self.max_per_window:
                    self.requests.append(current_time)
                    break
                wait_time = (self.requests[0] + self.window_size) - current_time
            await asyncio.sleep(wait_time + 0.01)

        await self.semaphore.acquire()
        try:
            yield
        finally:
            self.semaphore.release()

async def get_dual_limiter_pool() -> Dict[str, DualLimiter]:
    global _limiter_pool
    if _limiter_pool is not None:
        return _limiter_pool
    
    async with _pool_init_lock:
        if _limiter_pool is None:
            _limiter_pool = {
                GeminiModel.GEMINI_2_5_PRO: DualLimiter(
                    max_concurrent=RateLimits.RATE_LIMIT_2_5_PRO.value,
                    max_per_window=RateLimits.RATE_LIMIT_2_5_PRO.value,
                    window_size=RateLimits.RATE_LIMIT_WINDOW.value
                ),
                GeminiModel.GEMINI_2_5_FLASH: DualLimiter(
                    max_concurrent=RateLimits.RATE_LIMIT_2_5_FLASH.value,
                    max_per_window=RateLimits.RATE_LIMIT_2_5_FLASH.value,
                    window_size=RateLimits.RATE_LIMIT_WINDOW.value
                ),
                GeminiModel.GEMINI_2_5_FLASH_LITE: DualLimiter(
                    max_concurrent=RateLimits.RATE_LIMIT_2_5_FLASH_LITE.value,
                    max_per_window=RateLimits.RATE_LIMIT_2_5_FLASH_LITE.value,
                    window_size=RateLimits.RATE_LIMIT_WINDOW.value
                ),
            }
            
    return _limiter_pool