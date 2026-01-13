"""
Batch processor for converting multiple PDFs.

Handles parallel processing of queued conversion tasks.
"""

from pathlib import Path
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from threading import Lock

from batch.task_queue import TaskQueue, ConversionTask, TaskStatus
from core.converter import DoclingConverter, ConversionResult
from utils.logger import ProgressLogger

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Processes batch PDF conversions with parallel execution.

    Features:
    - Parallel processing with configurable worker count
    - Progress tracking and callbacks
    - Error handling and task retry
    - Memory-aware processing
    """

    def __init__(
        self,
        converter: DoclingConverter,
        max_workers: int = 4
    ):
        """
        Initialize batch processor.

        Args:
            converter: DoclingConverter instance to use
            max_workers: Maximum number of parallel workers
        """
        self.converter = converter
        self.max_workers = max_workers
        self._lock = Lock()
        self._results: List[ConversionResult] = []

    def process(
        self,
        queue: TaskQueue,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[ConversionResult]:
        """
        Process all tasks in the queue.

        Args:
            queue: TaskQueue with tasks to process
            progress_callback: Optional callback(current, total, message)

        Returns:
            List of ConversionResults
        """
        total_tasks = queue.pending_count
        if total_tasks == 0:
            logger.info("No pending tasks to process")
            return []

        self._results.clear()
        completed = 0

        logger.info(f"Starting batch processing of {total_tasks} task(s)")

        with ProgressLogger(logger, "Batch processing") as progress:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all pending tasks
                futures = {}
                for task in queue.get_pending():
                    future = executor.submit(self._process_task, task)
                    futures[future] = task

                # Process completed tasks
                for future in as_completed(futures):
                    task = futures[future]
                    try:
                        result = future.result()
                        with self._lock:
                            self._results.append(result)
                            completed += 1

                        if progress_callback:
                            message = f"Converted {task.source_name}"
                            if result.success:
                                message += f" ({result.pages_converted} pages)"
                            else:
                                message += f" - FAILED: {result.error_message}"
                            progress_callback(completed, total_tasks, message)

                    except Exception as e:
                        logger.error(f"Task {task.source_name} raised exception: {e}")
                        with self._lock:
                            completed += 1

                        if progress_callback:
                            progress_callback(completed, total_tasks, f"Error: {task.source_name}")

        return self._results

    def _process_task(self, task: ConversionTask) -> ConversionResult:
        """
        Process a single conversion task.

        Args:
            task: ConversionTask to process

        Returns:
            ConversionResult
        """
        task.mark_started()

        try:
            logger.info(f"Processing: {task.source_name}")

            result = self.converter.convert(
                task.source_path,
                task.output_dir,
                progress_callback=None
            )

            if result.success:
                task.mark_completed()
                logger.info(
                    f"Completed: {task.source_name} "
                    f"({result.pages_converted} pages, "
                    f"{result.images_extracted} images, "
                    f"{result.duration_seconds:.1f}s)"
                )
            else:
                task.mark_failed(result.error_message or "Unknown error")
                logger.error(f"Failed: {task.source_name} - {result.error_message}")

        except Exception as e:
            error_msg = str(e)
            task.mark_failed(error_msg)
            logger.error(f"Exception processing {task.source_name}: {e}")

            # Create failure result
            result = ConversionResult(
                success=False,
                source_path=task.source_path,
                output_path=Path(""),
                pages_converted=0,
                total_pages=0,
                images_extracted=0,
                duration_seconds=0,
                error_message=error_msg
            )

        return result

    def get_results(self) -> List[ConversionResult]:
        """Get all conversion results from the last batch."""
        return self._results.copy()

    def get_summary(self) -> dict:
        """
        Get summary statistics of the last batch.

        Returns:
            Dictionary with batch statistics
        """
        if not self._results:
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "total_pages": 0,
                "total_images": 0,
                "total_duration": 0,
            }

        successful = [r for r in self._results if r.success]
        failed = [r for r in self._results if not r.success]

        return {
            "total": len(self._results),
            "successful": len(successful),
            "failed": len(failed),
            "total_pages": sum(r.pages_converted for r in successful),
            "total_images": sum(r.images_extracted for r in successful),
            "total_duration": sum(r.duration_seconds for r in self._results),
        }
