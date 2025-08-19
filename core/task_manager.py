import asyncio
import logging
from typing import Dict, Tuple

TaskIdentifier = Tuple[int, int]  # (chat_id, message_id)

class TaskManager:
    def __init__(self):
        self._tasks: Dict[TaskIdentifier, asyncio.Task] = {}
        self.logger = logging.getLogger("TaskManager")

    def add_task(self, identifier: TaskIdentifier, task: asyncio.Task):
        self.logger.info(f"Adding task with identifier {identifier}")
        self._tasks[identifier] = task

    def cancel_task(self, identifier: TaskIdentifier) -> bool:
        task = self._tasks.get(identifier)
        if task and not task.done():
            self.logger.info(f"Cancelling task with identifier {identifier}")
            task.cancel()
            return True
        self.logger.warning(f"Task {identifier} not found or already done.")
        return False

    def remove_task(self, identifier: TaskIdentifier):
        if identifier in self._tasks:
            self.logger.info(f"Removing finished/cancelled task {identifier}")
            del self._tasks[identifier]

task_manager = TaskManager()