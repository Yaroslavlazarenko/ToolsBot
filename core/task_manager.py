import asyncio
import logging
from typing import Dict, Tuple

TaskIdentifier = Tuple[int, int]  # (chat_id, message_id)

class TaskManager:
    """Простой менеджер для отслеживания и отмены фоновых задач asyncio."""
    def __init__(self):
        self._tasks: Dict[TaskIdentifier, asyncio.Task] = {}
        self.logger = logging.getLogger("TaskManager")

    def add_task(self, identifier: TaskIdentifier, task: asyncio.Task):
        """Добавляет задачу в пул отслеживаемых."""
        self.logger.info(f"Adding task with identifier {identifier}")
        self._tasks[identifier] = task

    def cancel_task(self, identifier: TaskIdentifier) -> bool:
        """Находит и отменяет задачу по ее идентификатору."""
        task = self._tasks.get(identifier)
        if task and not task.done():
            self.logger.info(f"Cancelling task with identifier {identifier}")
            task.cancel()
            # Удаляем сразу после запроса на отмену
            del self._tasks[identifier]
            return True
        elif task:
            # Задача уже завершилась, просто удаляем
            del self._tasks[identifier]
        
        self.logger.warning(f"Task with identifier {identifier} not found or already done.")
        return False

    def remove_task(self, identifier: TaskIdentifier):
        """Удаляет задачу из пула (обычно после ее завершения)."""
        if identifier in self._tasks:
            self.logger.info(f"Removing finished/cancelled task {identifier}")
            del self._tasks[identifier]

# Создаем глобальный экземпляр, чтобы он был один на все приложение
task_manager = TaskManager()