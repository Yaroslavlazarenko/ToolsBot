import asyncio
from enum import Enum
from typing import Dict, Any

class AnalysisStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisManager:
    def __init__(self):
        # Структура: { "video_id": {"status": AnalysisStatus, "result": str | None, "event": asyncio.Event} }
        self._analyses: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()  # Для потокобезопасного создания записей

    async def get_or_create_analysis_entry(self, video_id: str) -> Dict[str, Any]:
        """Потокобезопасно получает или создает запись для анализа видео."""
        async with self._lock:
            if video_id not in self._analyses:
                self._analyses[video_id] = {
                    "status": AnalysisStatus.IN_PROGRESS,
                    "result": None,
                    "event": asyncio.Event()  # Событие для ожидания завершения
                }
            return self._analyses[video_id]

    async def complete_analysis(self, video_id: str, report_path: str):
        """Отмечает анализ как успешно завершенный и уведомляет всех ожидающих."""
        async with self._lock:
            if video_id in self._analyses:
                entry = self._analyses[video_id]
                entry["status"] = AnalysisStatus.COMPLETED
                entry["result"] = report_path
                entry["event"].set()  # "Поднимаем флаг" - будим всех, кто ждал

    async def fail_analysis(self, video_id: str, error_message: str):
        """Отмечает анализ как проваленный."""
        async with self._lock:
            if video_id in self._analyses:
                entry = self._analyses[video_id]
                entry["status"] = AnalysisStatus.FAILED
                entry["result"] = error_message
                entry["event"].set()

    async def cleanup_entry(self, video_id: str):
        """Удаляет запись из менеджера (можно вызывать через некоторое время)."""
        async with self._lock:
            if video_id in self._analyses:
                del self._analyses[video_id]

# Глобальный экземпляр для всего приложения
analysis_manager = AnalysisManager()