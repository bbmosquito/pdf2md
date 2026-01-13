"""
Task queue for managing batch PDF conversions.

Handles queuing, prioritization, and tracking of conversion tasks.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Callable, Iterator
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a conversion task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ConversionTask:
    """
    Represents a single PDF conversion task.

    Attributes:
        source_path: Path to the source PDF file
        output_dir: Output directory (optional, uses default if None)
        priority: Task priority (higher = processed first)
        status: Current task status
        error_message: Error message if failed
        created_at: Task creation timestamp
        started_at: Task start timestamp
        completed_at: Task completion timestamp
    """

    source_path: Path
    output_dir: Optional[Path] = None
    priority: int = 0
    status: TaskStatus = TaskStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def source_name(self) -> str:
        """Get the source file name."""
        return self.source_path.name

    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds (if completed)."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def mark_started(self) -> None:
        """Mark task as started."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def mark_completed(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()

    def mark_failed(self, error: str) -> None:
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now()

    def mark_skipped(self, reason: str) -> None:
        """Mark task as skipped."""
        self.status = TaskStatus.SKIPPED
        self.error_message = reason
        self.completed_at = datetime.now()


class TaskQueue:
    """
    Queue for managing batch conversion tasks.

    Features:
    - Priority-based task ordering
    - Add/remove tasks
    - Track task status
    - Filter tasks by status
    """

    def __init__(self):
        """Initialize an empty task queue."""
        self._tasks: List[ConversionTask] = []
        self._next_id = 0

    def add(
        self,
        source_path: str | Path,
        output_dir: Optional[str | Path] = None,
        priority: int = 0
    ) -> ConversionTask:
        """
        Add a task to the queue.

        Args:
            source_path: Path to PDF file
            output_dir: Optional output directory
            priority: Task priority (higher = processed first)

        Returns:
            The created ConversionTask
        """
        task = ConversionTask(
            source_path=Path(source_path),
            output_dir=Path(output_dir) if output_dir else None,
            priority=priority
        )
        self._tasks.append(task)
        logger.debug(f"Added task: {task.source_name}")
        return task

    def add_many(
        self,
        source_paths: List[str | Path],
        output_dir: Optional[str | Path] = None,
        priority: int = 0
    ) -> List[ConversionTask]:
        """
        Add multiple tasks to the queue.

        Args:
            source_paths: List of PDF file paths
            output_dir: Optional output directory for all tasks
            priority: Task priority for all tasks

        Returns:
            List of created ConversionTasks
        """
        tasks = []
        for path in source_paths:
            task = self.add(path, output_dir, priority)
            tasks.append(task)
        return tasks

    def add_from_directory(
        self,
        directory: str | Path,
        pattern: str = "*.pdf",
        recursive: bool = False,
        output_dir: Optional[str | Path] = None,
        priority: int = 0
    ) -> List[ConversionTask]:
        """
        Add all PDFs from a directory to the queue.

        Args:
            directory: Directory containing PDF files
            pattern: Glob pattern for matching files
            recursive: Whether to search recursively
            output_dir: Optional output directory
            priority: Task priority

        Returns:
            List of created ConversionTasks
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        if recursive:
            pdf_files = list(dir_path.rglob(pattern))
        else:
            pdf_files = list(dir_path.glob(pattern))

        tasks = []
        for pdf_file in pdf_files:
            task = self.add(pdf_file, output_dir, priority)
            tasks.append(task)

        logger.info(f"Added {len(tasks)} PDF(s) from {directory}")
        return tasks

    def remove(self, task: ConversionTask) -> bool:
        """
        Remove a task from the queue.

        Args:
            task: Task to remove

        Returns:
            True if task was removed, False if not found
        """
        try:
            self._tasks.remove(task)
            logger.debug(f"Removed task: {task.source_name}")
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """Clear all tasks from the queue."""
        self._tasks.clear()
        logger.debug("Cleared task queue")

    def get_pending(self) -> List[ConversionTask]:
        """Get all pending tasks, sorted by priority."""
        pending = [t for t in self._tasks if t.status == TaskStatus.PENDING]
        pending.sort(key=lambda t: (-t.priority, t.created_at))
        return pending

    def get_by_status(self, status: TaskStatus) -> List[ConversionTask]:
        """Get all tasks with a specific status."""
        return [t for t in self._tasks if t.status == status]

    def get_completed(self) -> List[ConversionTask]:
        """Get all completed tasks."""
        return self.get_by_status(TaskStatus.COMPLETED)

    def get_failed(self) -> List[ConversionTask]:
        """Get all failed tasks."""
        return self.get_by_status(TaskStatus.FAILED)

    def __iter__(self) -> Iterator[ConversionTask]:
        """Iterate over all tasks."""
        return iter(self._tasks)

    def __len__(self) -> int:
        """Get total number of tasks."""
        return len(self._tasks)

    @property
    def pending_count(self) -> int:
        """Get number of pending tasks."""
        return len(self.get_pending())

    @property
    def completed_count(self) -> int:
        """Get number of completed tasks."""
        return len(self.get_completed())

    @property
    def failed_count(self) -> int:
        """Get number of failed tasks."""
        return len(self.get_failed())

    def get_statistics(self) -> dict:
        """
        Get queue statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total": len(self._tasks),
            "pending": self.pending_count,
            "running": len(self.get_by_status(TaskStatus.RUNNING)),
            "completed": self.completed_count,
            "failed": self.failed_count,
            "skipped": len(self.get_by_status(TaskStatus.SKIPPED)),
        }
