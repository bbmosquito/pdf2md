"""
Memory Manager for handling large PDF files.

Monitors and controls memory usage during PDF processing.
"""

import psutil
import os
from typing import Optional, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Current memory statistics."""
    used_mb: float
    available_mb: float
    percent: float
    process_mb: float


class MemoryManager:
    """
    Manages memory usage during PDF processing.

    Features:
    - Monitors system and process memory
    - Provides recommendations for chunk sizes
    - Warns when approaching memory limits
    """

    def __init__(
        self,
        max_percent: float = 85.0,
        max_process_mb: float = 8192,  # 8GB default for process
        enable_monitoring: bool = True
    ):
        """
        Initialize Memory Manager.

        Args:
            max_percent: Maximum system memory percentage to use
            max_process_mb: Maximum process memory in MB
            enable_monitoring: Enable active memory monitoring
        """
        self.max_percent = max_percent
        self.max_process_mb = max_process_mb
        self.enable_monitoring = enable_monitoring
        self.process = psutil.Process(os.getpid())

    def get_stats(self) -> MemoryStats:
        """Get current memory statistics."""
        sys_mem = psutil.virtual_memory()
        proc_mem = self.process.memory_info()

        return MemoryStats(
            used_mb=sys_mem.used / 1024 / 1024,
            available_mb=sys_mem.available / 1024 / 1024,
            percent=sys_mem.percent,
            process_mb=proc_mem.rss / 1024 / 1024
        )

    def check_memory(self) -> bool:
        """
        Check if current memory usage is acceptable.

        Returns:
            True if memory is OK, False if approaching limits
        """
        if not self.enable_monitoring:
            return True

        stats = self.get_stats()

        # Check system memory
        if stats.percent >= self.max_percent:
            logger.warning(
                f"System memory at {stats.percent:.1f}% "
                f"(limit: {self.max_percent}%)"
            )
            return False

        # Check process memory
        if stats.process_mb >= self.max_process_mb:
            logger.warning(
                f"Process memory at {stats.process_mb:.1f}MB "
                f"(limit: {self.max_process_mb}MB)"
            )
            return False

        return True

    def recommend_chunk_size(
        self,
        base_size: int = 5,
        min_size: int = 1,
        max_size: int = 20
    ) -> int:
        """
        Recommend an optimal chunk size based on current memory.

        Args:
            base_size: Base/default chunk size
            min_size: Minimum chunk size
            max_size: Maximum chunk size

        Returns:
            Recommended chunk size
        """
        if not self.enable_monitoring:
            return base_size

        stats = self.get_stats()

        # Scale down if memory is high
        if stats.percent > 70:
            scale = 0.5
        elif stats.percent > 50:
            scale = 0.75
        else:
            scale = 1.0

        chunk_size = int(base_size * scale)
        return max(min_size, min(chunk_size, max_size))

    def get_memory_pressure(self) -> str:
        """
        Get current memory pressure level.

        Returns:
            'low', 'medium', 'high', or 'critical'
        """
        stats = self.get_stats()

        if stats.percent < 50:
            return "low"
        elif stats.percent < 70:
            return "medium"
        elif stats.percent < 85:
            return "high"
        else:
            return "critical"

    def log_stats(self, context: str = "") -> None:
        """Log current memory statistics with optional context."""
        stats = self.get_stats()
        pressure = self.get_memory_pressure()

        logger.info(
            f"Memory {context}: "
            f"Process: {stats.process_mb:.1f}MB | "
            f"System: {stats.percent:.1f}% | "
            f"Pressure: {pressure}"
        )

    def with_memory_check(self, func: Callable) -> Callable:
        """
        Decorator to add memory checking to a function.

        Usage:
            @memory_manager.with_memory_check
            def process_pages(pages):
                ...
        """
        def wrapper(*args, **kwargs):
            if not self.check_memory():
                logger.warning(
                    "Memory pressure high, consider reducing chunk size"
                )
            return func(*args, **kwargs)
        return wrapper
