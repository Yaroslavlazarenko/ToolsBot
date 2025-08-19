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
        # 1. Создаем блокировку для каждого экземпляра лимитера
        self._lock = asyncio.Lock()

    async def allow_request(self) -> bool:
        # 2. Используем 'async with' для захвата блокировки.
        # Это гарантирует, что только одна корутина может быть внутри этого блока.
        async with self._lock:
            current_time = time.time()
            
            # Чистим старые запросы
            while self.requests and self.requests[0] <= current_time - self.window_size:
                self.requests.popleft()
            
            # Проверяем и добавляем новый запрос
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

import asyncio
from contextlib import asynccontextmanager

class ConcurrencyLimiter:
    """
    Лимитер, который ограничивает количество одновременно выполняющихся задач.
    
    Он использует семафор для контроля доступа. Код, который хочет выполнить
    запрос, должен сначала "захватить" слот у семафора. Слот освобождается
    только после того, как запрос завершится (успешно или с ошибкой).
    """
    def __init__(self, max_concurrent_requests: int):
        if max_concurrent_requests <= 0:
            raise ValueError("Maximum concurrent requests must be positive.")
        # max_concurrent_requests - это наш "лимит" из RateLimits.
        # Например, если значение 15, то одновременно может выполняться не более 15 запросов.
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        print(f"ConcurrencyLimiter initialized with a limit of {max_concurrent_requests} concurrent requests.")

    @asynccontextmanager
    async def request_slot(self):
        """
        Асинхронный контекстный менеджер для получения "слота" на выполнение запроса.
        
        Использование:
        async with limiter.request_slot():
            # ... код отправки запроса ...
            
        Этот паттерн гарантирует, что семафор будет освобожден,
        даже если внутри блока 'with' произойдет ошибка.
        """
        # Блокирует выполнение, если все слоты заняты.
        # Как только слот освобождается, корутина продолжает работу.
        await self.semaphore.acquire()
        try:
            # Передаем управление коду внутри блока 'with'
            yield
        finally:
            # Этот блок выполнится всегда, освобождая слот для следующей задачи.
            self.semaphore.release()

# Поместите эту функцию рядом со старой get_limiter_pool
async def get_concurrency_limiter_pool() -> Dict[str, ConcurrencyLimiter]:
    global _limiter_pool
    # Используем ту же глобальную переменную, чтобы не плодить сущности
    if _limiter_pool is not None:
        return _limiter_pool
    async with _pool_init_lock:
        if _limiter_pool is None:
            print("Initializing Concurrency Limiter Pool...")
            # Значения из RateLimits теперь означают "максимальное число одновременных запросов"
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
    """
    Комбинированный лимитер, который одновременно отслеживает:
    1. Количество одновременных запросов (с помощью семафора).
    2. Частоту запросов в минуту (с помощью скользящего окна).

    Это позволяет избежать как мгновенной перегрузки, так и превышения
    официальных лимитов API в течение минуты.
    """
    def __init__(self, max_concurrent: int, max_per_window: int, window_size: int):
        if max_concurrent <= 0 or max_per_window <= 0:
            raise ValueError("Limiter values must be positive.")
        
        # 1. Лимитер одновременных запросов
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # 2. Лимитер скользящего окна
        self.requests = deque()
        self.max_per_window = max_per_window
        self.window_size = window_size
        self._window_lock = asyncio.Lock() # Блокировка для защиты deque
        
        print(
            f"DualLimiter initialized: "
            f"{max_concurrent} concurrent requests, "
            f"{max_per_window} requests per {window_size}s window."
        )

    @asynccontextmanager
    async def request_slot(self):
        """
        Асинхронный контекстный менеджер для получения слота на выполнение.

        Гарантирует, что перед выполнением кода будут соблюдены оба лимита.
        """
        # --- Шаг 1: Дождаться места в скользящем окне (RPM лимит) ---
        while True:
            async with self._window_lock:
                current_time = time.time()
                
                # Очищаем старые временные метки
                while self.requests and self.requests[0] <= current_time - self.window_size:
                    self.requests.popleft()
                
                # Если есть место в окне, резервируем его и выходим из цикла
                if len(self.requests) < self.max_per_window:
                    self.requests.append(current_time)
                    break
                
                # Если места нет, вычисляем, сколько нужно ждать
                wait_time = (self.requests[0] + self.window_size) - current_time
            
            # Ждем вне блокировки, чтобы не мешать другим проверкам
            await asyncio.sleep(wait_time + 0.01) # Добавляем небольшой буфер

        # --- Шаг 2: Захватить слот на одновременное выполнение ---
        await self.semaphore.acquire()
        
        try:
            # Все лимиты соблюдены, можно выполнять запрос
            yield
        finally:
            # --- Шаг 3: Освободить слот на одновременное выполнение ---
            # Слот в скользящем окне освободится сам со временем.
            self.semaphore.release()


# --- НОВАЯ ФАБРИЧНАЯ ФУНКЦИЯ ---

async def get_dual_limiter_pool() -> Dict[str, DualLimiter]:
    """
    Создает и возвращает пул комбинированных лимитеров (DualLimiter).
    """
    global _limiter_pool
    if _limiter_pool is not None:
        return _limiter_pool
    
    async with _pool_init_lock:
        # Повторная проверка на случай, если другой поток уже создал пул
        if _limiter_pool is None:
            print("Initializing Dual Limiter Pool...")
            
            # Здесь можно задать разные значения для одновременных и минутных лимитов,
            # но для простоты используем одно и то же значение из RateLimits.
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
