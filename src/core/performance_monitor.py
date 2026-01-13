"""
Performance Monitor for PDF2MD

Real-time monitoring of CPU, memory, and conversion progress.
Helps identify bottlenecks and optimal configurations.
"""

import psutil
import time
import threading
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceSnapshot:
    """Single snapshot of system performance."""
    timestamp: datetime
    cpu_percent: float
    memory_available_gb: float
    memory_percent: float
    memory_used_gb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    conversion_progress: Optional[float] = None
    conversion_message: Optional[str] = None


@dataclass
class PerformanceStats:
    """Aggregated performance statistics."""
    duration_seconds: float
    cpu_avg: float
    cpu_max: float
    memory_avg_gb: float
    memory_max_gb: float
    memory_peak_gb: float
    snapshots: List[PerformanceSnapshot] = field(default_factory=list)

    @property
    def memory_efficiency(self) -> float:
        """Calculate memory efficiency (lower is better)."""
        if self.memory_avg_gb > 0 and self.duration_seconds > 0:
            return self.memory_avg_gb * self.duration_seconds
        return 0.0


class PerformanceMonitor:
    """
    Real-time performance monitor for conversion process.

    Tracks CPU, memory, disk I/O, and conversion progress.

    Usage:
        monitor = PerformanceMonitor()
        monitor.start()

        # Run conversion
        result = converter.convert(...)

        monitor.stop()
        stats = monitor.get_statistics()
        monitor.print_summary()
    """

    def __init__(
        self,
        sample_interval: float = 1.0,
        enable_disk_monitoring: bool = True
    ):
        """
        Initialize performance monitor.

        Args:
            sample_interval: Time between samples (seconds)
            enable_disk_monitoring: Whether to track disk I/O
        """
        self.sample_interval = sample_interval
        self.enable_disk_monitoring = enable_disk_monitoring

        self.snapshots: List[PerformanceSnapshot] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Initial disk I/O counters
        self._initial_disk_io = None

        # Progress callback
        self._progress_callback: Optional[Callable[[float, str], None]] = None

    def start(self):
        """Start monitoring in background thread."""
        if self._running:
            logger.warning("Monitor is already running")
            return

        self._running = True

        if self.enable_disk_monitoring:
            self._initial_disk_io = psutil.disk_io_counters()

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

        logger.info("Performance monitoring started")

    def stop(self):
        """Stop monitoring and wait for thread to finish."""
        if not self._running:
            return

        self._running = False

        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

        logger.info(f"Performance monitoring stopped. Collected {len(self.snapshots)} snapshots")

    def _monitor_loop(self):
        """Background monitoring loop."""
        process = psutil.Process()
        system_memory = psutil.virtual_memory()

        while self._running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)

                # Memory
                system_memory = psutil.virtual_memory()
                memory_available_gb = system_memory.available / (1024**3)
                memory_percent = system_memory.percent
                memory_used_gb = system_memory.used / (1024**3)

                # Disk I/O (since start)
                disk_read_mb = 0.0
                disk_write_mb = 0.0

                if self.enable_disk_monitoring and self._initial_disk_io:
                    current_io = psutil.disk_io_counters()
                    if current_io and self._initial_disk_io:
                        disk_read_mb = (current_io.read_bytes - self._initial_disk_io.read_bytes) / (1024**2)
                        disk_write_mb = (current_io.write_bytes - self._initial_disk_io.write_bytes) / (1024**2)

                # Create snapshot
                snapshot = PerformanceSnapshot(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_available_gb=memory_available_gb,
                    memory_percent=memory_percent,
                    memory_used_gb=memory_used_gb,
                    disk_io_read_mb=disk_read_mb,
                    disk_io_write_mb=disk_write_mb
                )

                self.snapshots.append(snapshot)

                # Sleep until next sample
                time.sleep(self.sample_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.sample_interval)

    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """
        Set progress callback for conversion progress.

        The callback will be called with (progress, message) from the monitor.

        Args:
            callback: Function accepting (progress: float, message: str)
        """
        self._progress_callback = callback

    def update_progress(self, progress: float, message: str):
        """
        Update conversion progress (called from conversion thread).

        Args:
            progress: Progress value (0.0 to 1.0)
            message: Progress message
        """
        if self.snapshots:
            # Update latest snapshot with progress info
            self.snapshots[-1].conversion_progress = progress
            self.snapshots[-1].conversion_message = message

        # Forward to callback if set
        if self._progress_callback:
            self._progress_callback(progress, message)

    def get_statistics(self) -> PerformanceStats:
        """
        Calculate aggregated statistics from snapshots.

        Returns:
            PerformanceStats with aggregated metrics
        """
        if not self.snapshots:
            return PerformanceStats(
                duration_seconds=0,
                cpu_avg=0,
                cpu_max=0,
                memory_avg_gb=0,
                memory_max_gb=0,
                memory_peak_gb=0
            )

        # Time span
        start_time = self.snapshots[0].timestamp
        end_time = self.snapshots[-1].timestamp
        duration = (end_time - start_time).total_seconds()

        # CPU stats
        cpu_values = [s.cpu_percent for s in self.snapshots]
        cpu_avg = sum(cpu_values) / len(cpu_values)
        cpu_max = max(cpu_values)

        # Memory stats
        memory_values = [s.memory_used_gb for s in self.snapshots]
        memory_avg = sum(memory_values) / len(memory_values)
        memory_max = max(memory_values)
        memory_peak = memory_max  # Same as max for now

        return PerformanceStats(
            duration_seconds=duration,
            cpu_avg=cpu_avg,
            cpu_max=cpu_max,
            memory_avg_gb=memory_avg,
            memory_max_gb=memory_max,
            memory_peak_gb=memory_peak,
            snapshots=self.snapshots.copy()
        )

    def print_summary(self):
        """Print performance summary."""
        stats = self.get_statistics()

        print("\n" + "=" * 70)
        print(" Performance Summary")
        print("=" * 70)

        print(f"\nDuration: {stats.duration_seconds:.1f} seconds")

        print(f"\nCPU Usage:")
        print(f"  Average: {stats.cpu_avg:.1f}%")
        print(f"  Peak:    {stats.cpu_max:.1f}%")

        print(f"\nMemory Usage:")
        print(f"  Average: {stats.memory_avg_gb:.1f} GB")
        print(f"  Peak:    {stats.memory_max_gb:.1f} GB")

        if self.enable_disk_monitoring and stats.snapshots:
            final_snapshot = stats.snapshots[-1]
            print(f"\nDisk I/O:")
            print(f"  Read:  {final_snapshot.disk_io_read_mb:.1f} MB")
            print(f"  Write: {final_snapshot.disk_io_write_mb:.1f} MB")

        print("\n" + "=" * 70 + "\n")

    def print_detailed_timeline(self):
        """Print detailed timeline of snapshots."""
        if not self.snapshots:
            print("No snapshots available")
            return

        print("\n" + "=" * 100)
        print(" Detailed Performance Timeline")
        print("=" * 100)

        print(f"\n{'Time':<20} {'CPU%':<8} {'Mem(GB)':<12} {'Mem%':<8} {'DiskR(MB)':<12} {'DiskW(MB)':<12} {'Progress':<12}")
        print("-" * 100)

        for snapshot in self.snapshots:
            time_str = snapshot.timestamp.strftime("%H:%M:%S")
            progress_str = f"{snapshot.conversion_progress*100:.0f}%" if snapshot.conversion_progress else "N/A"

            print(f"{time_str:<20} "
                  f"{snapshot.cpu_percent:<8.1f} "
                  f"{snapshot.memory_used_gb:<12.2f} "
                  f"{snapshot.memory_percent:<8.1f} "
                  f"{snapshot.disk_io_read_mb:<12.1f} "
                  f"{snapshot.disk_io_write_mb:<12.1f} "
                  f"{progress_str:<12}")

        print("=" * 100 + "\n")

    def save_to_file(self, filepath: str):
        """
        Save performance data to file.

        Args:
            filepath: Path to save the data (CSV format)
        """
        import csv

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Timestamp', 'CPU_Percent', 'Memory_Available_GB',
                'Memory_Percent', 'Memory_Used_GB', 'Disk_Read_MB',
                'Disk_Write_MB', 'Conversion_Progress', 'Conversion_Message'
            ])

            # Data
            for snapshot in self.snapshots:
                writer.writerow([
                    snapshot.timestamp.isoformat(),
                    snapshot.cpu_percent,
                    snapshot.memory_available_gb,
                    snapshot.memory_percent,
                    snapshot.memory_used_gb,
                    snapshot.disk_io_read_mb,
                    snapshot.disk_io_write_mb,
                    snapshot.conversion_progress,
                    snapshot.conversion_message
                ])

        logger.info(f"Performance data saved to {filepath}")

    def get_memory_pressure_events(self) -> List[PerformanceSnapshot]:
        """
        Get snapshots where memory pressure was high.

        Returns:
            List of snapshots with memory usage > 80%
        """
        return [s for s in self.snapshots if s.memory_percent > 80]

    def get_cpu_bottleneck_periods(self) -> List[PerformanceSnapshot]:
        """
        Get snapshots where CPU was saturated.

        Returns:
            List of snapshots with CPU usage > 90%
        """
        return [s for s in self.snapshots if s.cpu_percent > 90]


def monitor_conversion(
    converter_func: Callable,
    *args,
    sample_interval: float = 1.0,
    **kwargs
):
    """
    Convenience function to monitor a conversion.

    Usage:
        def convert_pdf():
            return converter.convert(pdf_path, output_path)

        result, stats = monitor_conversion(convert_pdf)
        stats.print_summary()

    Args:
        converter_func: Function to run (should take no arguments)
        *args: Arguments to pass to converter_func
        sample_interval: Monitoring sample interval
        **kwargs: Keyword arguments to pass to converter_func

    Returns:
        Tuple of (result, PerformanceStats)
    """
    monitor = PerformanceMonitor(sample_interval=sample_interval)
    monitor.start()

    try:
        result = converter_func(*args, **kwargs)
    finally:
        monitor.stop()

    stats = monitor.get_statistics()
    return result, stats


if __name__ == "__main__":
    # Test the monitor
    print("Testing PerformanceMonitor...")

    monitor = PerformanceMonitor(sample_interval=0.5)
    monitor.start()

    print("Monitoring for 5 seconds...")
    time.sleep(5)

    monitor.stop()
    monitor.print_summary()
    monitor.print_detailed_timeline()
