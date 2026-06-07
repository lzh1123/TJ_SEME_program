from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional

from ...domain.ids import new_id

logger = logging.getLogger(__name__)

TaskStatus = Literal["pending", "processing", "completed", "failed"]


@dataclass
class ImportTask:
    task_id: str
    status: TaskStatus = "pending"
    total: int = 0
    processed: int = 0
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "total": self.total,
            "processed": self.processed,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ImportTaskQueue:
    """Simple in-memory async task queue for KB document imports."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: Dict[str, ImportTask] = {}
        self._worker_task: Optional[asyncio.Task] = None
        self._handler: Optional[Callable] = None

    def set_handler(self, handler: Callable[[List[Path], ImportTask], Any]) -> None:
        """Set the async handler that processes a batch of files."""
        self._handler = handler

    async def start(self) -> None:
        """Start the background worker."""
        if self._worker_task is not None:
            return
        self._worker_task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the background worker."""
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

    def enqueue(self, items: List[Any]) -> str:
        """Enqueue items for import. Each item is typically (temp_path, original_name).
        Returns task_id for status polling."""
        task_id = new_id("import")
        task = ImportTask(task_id=task_id, total=len(items))
        self._tasks[task_id] = task
        self._queue.put_nowait((task_id, items))
        logger.info("Enqueued import task %s with %d items", task_id, len(items))
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status by id. Returns None if not found."""
        task = self._tasks.get(task_id)
        if task is None:
            return None
        return task.to_dict()

    async def _run(self) -> None:
        """Background worker loop."""
        logger.info("Import task queue worker started")
        while True:
            try:
                task_id, file_paths = await self._queue.get()
                task = self._tasks.get(task_id)
                if task is None:
                    continue

                task.status = "processing"
                logger.info("Processing import task %s", task_id)

                try:
                    if self._handler is not None:
                        await self._handler(file_paths, task)
                    task.status = "completed"
                except Exception as e:
                    logger.error("Import task %s failed: %s", task_id, e)
                    task.status = "failed"
                    task.errors.append(f"{type(e).__name__}: {e}")

                task.completed_at = datetime.now(timezone.utc)
            except asyncio.CancelledError:
                logger.info("Import task queue worker stopping")
                return
            except Exception as e:
                logger.error("Import task worker error: %s", e)


# Module-level singleton
_import_queue: Optional[ImportTaskQueue] = None


def get_import_queue() -> ImportTaskQueue:
    global _import_queue
    if _import_queue is None:
        _import_queue = ImportTaskQueue()
    return _import_queue
