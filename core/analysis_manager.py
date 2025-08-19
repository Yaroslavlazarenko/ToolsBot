import asyncio
from enum import Enum
from typing import Dict, Any

class AnalysisStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisManager:
    def __init__(self):
        self._analyses: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_analysis_entry(self, video_id: str) -> Dict[str, Any]:
        async with self._lock:
            if video_id not in self._analyses:
                self._analyses[video_id] = {
                    "status": AnalysisStatus.IN_PROGRESS,
                    "result": None,
                    "event": asyncio.Event()
                }
            return self._analyses[video_id]

    async def complete_analysis(self, video_id: str, report_path: str):
        async with self._lock:
            if video_id in self._analyses:
                entry = self._analyses[video_id]
                entry["status"] = AnalysisStatus.COMPLETED
                entry["result"] = report_path
                entry["event"].set()

    async def fail_analysis(self, video_id: str, error_message: str):
        async with self._lock:
            if video_id in self._analyses:
                entry = self._analyses[video_id]
                entry["status"] = AnalysisStatus.FAILED
                entry["result"] = error_message
                entry["event"].set()

    async def cleanup_entry(self, video_id: str):
        async with self._lock:
            if video_id in self._analyses:
                del self._analyses[video_id]

analysis_manager = AnalysisManager()