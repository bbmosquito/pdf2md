"""
AMD CPU Performance Benchmark Script

Tests different batch size and worker configurations to find optimal settings
for the AMD Ryzen 9 3950X/3990X (16-core) system.

Usage:
    python benchmark_amd_cpu.py --pdf report.pdf
    python benchmark_amd_cpu.py --pdf report.pdf --quick
"""

import sys
import time
import psutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from core.converter import DoclingConverter, ConversionConfig
from core.cpu_optimizer import AMDCPUOptimizer

if RICH_AVAILABLE:
    console = Console()
else:
    console = None

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    batch_size: int
    workers: int
    gpu_enabled: bool
    duration_seconds: float
    memory_used_gb: float
    cpu_percent: float
    pages_converted: int
    total_pages: int
    success: bool
    error_message: Optional[str] = None

    @property
    def throughput_pages_per_sec(self) -> float:
        """Calculate throughput in pages per second."""
        if self.duration_seconds > 0 and self.pages_converted > 0:
            return self.pages_converted / self.duration_seconds
        return 0.0


class CPUBenchmark:
    """CPU Performance Benchmark Suite."""

    # Test configurations matrix
    DEFAULT_CONFIGS = [
        # (batch_size, workers, description)
        (4, 4, "Conservative"),
        (8, 8, "Safe"),
        (16, 12, "Moderate"),
        (24, 16, "Recommended"),
        (32, 16, "Optimized"),
        (48, 16, "Aggressive"),
    ]

    def __init__(self, pdf_path: Path):
        """
        Initialize benchmark suite.

        Args:
            pdf_path: Path to PDF file for testing
        """
        self.pdf_path = pdf_path
        self.results: List[BenchmarkResult] = []
        self.optimizer = AMDCPUOptimizer()

    def print_system_info(self):
        """Print system information."""
        if console:
            console.print(Panel.fit(
                f"[bold cyan]System Information[/bold cyan]\n\n"
                f"Physical Cores: {self.optimizer.system.physical_cores}\n"
                f"Logical Cores: {self.optimizer.system.logical_cores}\n"
                f"Total Memory: {self.optimizer.system.total_memory_gb:.1f} GB\n"
                f"Available Memory: {self.optimizer.system.available_memory_gb:.1f} GB\n"
                f"Test PDF: {self.pdf_path.name}",
                title="🖥️  Benchmark Setup",
                border_style="cyan"
            ))
        else:
            print(f"\n{'='*60}")
            print("System Information")
            print(f"{'='*60}")
            print(f"Physical Cores: {self.optimizer.system.physical_cores}")
            print(f"Logical Cores: {self.optimizer.system.logical_cores}")
            print(f"Total Memory: {self.optimizer.system.total_memory_gb:.1f} GB")
            print(f"Available Memory: {self.optimizer.system.available_memory_gb:.1f} GB")
            print(f"Test PDF: {self.pdf_path.name}")
            print(f"{'='*60}\n")

    def print_optimizer_recommendation(self):
        """Print the optimizer's recommended configuration."""
        config = self.optimizer.get_optimal_config(enable_gpu=False)

        if console:
            console.print(Panel.fit(
                f"[bold green]🚀 Optimizer Recommendation[/bold green]\n\n"
                f"Workers: [cyan]{config.max_workers}[/cyan]\n"
                f"Threads: [cyan]{config.num_threads}[/cyan]\n"
                f"OCR Batch Size: [cyan]{config.ocr_batch_size}[/cyan]\n"
                f"Layout Batch Size: [cyan]{config.layout_batch_size}[/cyan]\n"
                f"Table Batch Size: [cyan]{config.table_batch_size}[/cyan]\n"
                f"Max Process Memory: [cyan]{config.max_process_memory_gb:.1f} GB[/cyan]",
                title="Recommended Configuration",
                border_style="green"
            ))
        else:
            print(f"\n{'='*60}")
            print("Optimizer Recommendation")
            print(f"{'='*60}")
            print(f"Workers: {config.max_workers}")
            print(f"Threads: {config.num_threads}")
            print(f"OCR Batch Size: {config.ocr_batch_size}")
            print(f"Layout Batch Size: {config.layout_batch_size}")
            print(f"Table Batch Size: {config.table_batch_size}")
            print(f"Max Process Memory: {config.max_process_memory_gb:.1f} GB")
            print(f"{'='*60}\n")

    def run_single_benchmark(
        self,
        batch_size: int,
        workers: int,
        enable_gpu: bool = False
    ) -> BenchmarkResult:
        """
        Run a single benchmark with given configuration.

        Args:
            batch_size: Batch size for OCR/Layout processing
            workers: Number of worker processes
            enable_gpu: Whether to enable GPU

        Returns:
            BenchmarkResult with performance metrics
        """
        if console:
            console.print(f"\n[bold yellow]Testing:[/bold yellow] "
                        f"batch_size={batch_size}, workers={workers}, gpu={enable_gpu}")

        # Record initial state
        initial_mem = psutil.virtual_memory().available / (1024**3)
        start_time = time.time()

        # Create configuration
        config = ConversionConfig(
            ocr_enabled=True,
            dpi=200,
            max_workers=workers,
            enable_gpu=enable_gpu,
            accelerator_device="cpu",
            ocr_batch_size=batch_size,
            layout_batch_size=batch_size,
            table_batch_size=max(batch_size // 4, 2),
            num_threads=self.optimizer.system.logical_cores
        )

        # Create converter
        try:
            converter = DoclingConverter(config)
        except Exception as e:
            if console:
                console.print(f"[red]Failed to initialize converter: {e}[/red]")
            return BenchmarkResult(
                batch_size=batch_size,
                workers=workers,
                gpu_enabled=enable_gpu,
                duration_seconds=0,
                memory_used_gb=0,
                cpu_percent=0,
                pages_converted=0,
                total_pages=0,
                success=False,
                error_message=str(e)
            )

        # Prepare output path
        output_dir = Path("benchmark_outputs")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"test_batch{batch_size}_w{workers}.md"

        # Run conversion
        success = False
        error_msg = None
        pages_converted = 0
        total_pages = 0

        try:
            result = converter.convert(
                self.pdf_path,
                output_file,
                progress_callback=None  # Disable for benchmark
            )
            success = result.success
            pages_converted = result.pages_converted
            total_pages = result.total_pages
            error_msg = result.error_message

        except Exception as e:
            error_msg = str(e)
            success = False

        end_time = time.time()
        duration = end_time - start_time

        # Record final state
        final_mem = psutil.virtual_memory().available / (1024**3)
        mem_used = initial_mem - final_mem

        # Get average CPU usage during conversion
        cpu_percent = psutil.cpu_percent(interval=0.1)

        result = BenchmarkResult(
            batch_size=batch_size,
            workers=workers,
            gpu_enabled=enable_gpu,
            duration_seconds=duration,
            memory_used_gb=mem_used,
            cpu_percent=cpu_percent,
            pages_converted=pages_converted,
            total_pages=total_pages,
            success=success,
            error_message=error_msg
        )

        # Print immediate result
        if success:
            if console:
                console.print(f"[green]✓ Success[/green] | "
                            f"Time: {duration:.1f}s | "
                            f"Memory: {mem_used:.1f}GB | "
                            f"Throughput: {result.throughput_pages_per_sec:.2f} pages/s")
            else:
                print(f"✓ Success | Time: {duration:.1f}s | Memory: {mem_used:.1f}GB | "
                      f"Throughput: {result.throughput_pages_per_sec:.2f} pages/s")
        else:
            if console:
                console.print(f"[red]✗ Failed[/red] | {error_msg}")
            else:
                print(f"✗ Failed | {error_msg}")

        return result

    def run_full_benchmark(self, configs: Optional[List[Tuple[int, int, str]]] = None):
        """
        Run full benchmark suite.

        Args:
            configs: Optional list of (batch_size, workers, description) tuples
                    If None, uses DEFAULT_CONFIGS
        """
        if configs is None:
            configs = self.DEFAULT_CONFIGS

        self.print_system_info()
        self.print_optimizer_recommendation()

        if console:
            console.print(f"\n[bold]Running {len(configs)} benchmark configurations...[/bold]\n")
        else:
            print(f"\nRunning {len(configs)} benchmark configurations...\n")

        for batch_size, workers, description in configs:
            result = self.run_single_benchmark(batch_size, workers, enable_gpu=False)
            result.description = description  # Add description tag
            self.results.append(result)

            # Force garbage collection between runs
            import gc
            gc.collect()

        self.print_summary()

    def run_quick_benchmark(self):
        """Run a quick benchmark with 3 key configurations."""
        configs = [
            (8, 8, "Safe"),
            (32, 16, "Optimized"),
            (48, 16, "Aggressive"),
        ]

        if console:
            console.print("[bold yellow]Quick Benchmark Mode[/bold yellow]\n")

        self.run_full_benchmark(configs)

    def print_summary(self):
        """Print benchmark summary."""
        if console:
            self._print_rich_summary()
        else:
            self._print_simple_summary()

    def _print_rich_summary(self):
        """Print summary with rich formatting."""
        # Create results table
        table = Table(title="\n🏆 Benchmark Results Summary")
        table.add_column("Config", style="cyan")
        table.add_column("Batch", style="cyan")
        table.add_column("Workers", style="cyan")
        table.add_column("Time (s)", style="green")
        table.add_column("Memory (GB)", style="yellow")
        table.add_column("CPU %", style="blue")
        table.add_column("Pages/s", style="magenta")
        table.add_column("Status", style="bold")

        for result in self.results:
            description = getattr(result, 'description', '')
            status = "[green]✓[/green]" if result.success else "[red]✗[/red]"

            table.add_row(
                description,
                str(result.batch_size),
                str(result.workers),
                f"{result.duration_seconds:.1f}" if result.success else "N/A",
                f"{result.memory_used_gb:.1f}" if result.success else "N/A",
                f"{result.cpu_percent:.0f}" if result.success else "N/A",
                f"{result.throughput_pages_per_sec:.2f}" if result.success else "N/A",
                status
            )

        console.print(table)

        # Find best configuration
        successful = [r for r in self.results if r.success]
        if successful:
            best = min(successful, key=lambda x: x.duration_seconds)

            console.print(Panel.fit(
                f"[bold green]🎯 Best Configuration[/bold green]\n\n"
                f"Batch Size: [cyan]{best.batch_size}[/cyan]\n"
                f"Workers: [cyan]{best.workers}[/cyan]\n"
                f"Duration: [green]{best.duration_seconds:.1f}s[/green]\n"
                f"Throughput: [magenta]{best.throughput_pages_per_sec:.2f} pages/s[/magenta]\n"
                f"Memory Used: [yellow]{best.memory_used_gb:.1f} GB[/yellow]",
                title="Recommended",
                border_style="green"
            ))

        # Performance comparison
        if len(successful) >= 2:
            fastest = min(successful, key=lambda x: x.duration_seconds)
            slowest = max(successful, key=lambda x: x.duration_seconds)
            speedup = slowest.duration_seconds / fastest.duration_seconds

            console.print(f"\n[bold]Performance Improvement:[/bold] "
                        f"[green]{speedup:.1f}x[/green] faster than slowest config")

    def _print_simple_summary(self):
        """Print simple text summary."""
        print(f"\n{'='*80}")
        print("Benchmark Results Summary")
        print(f"{'='*80}")

        print(f"\n{'Config':<15} {'Batch':<8} {'Workers':<8} {'Time(s)':<10} {'Mem(GB)':<10} {'Pages/s':<12} {'Status'}")
        print("-" * 80)

        for result in self.results:
            description = getattr(result, 'description', '')
            status = "✓" if result.success else "✗"

            if result.success:
                print(f"{description:<15} {result.batch_size:<8} {result.workers:<8} "
                      f"{result.duration_seconds:<10.1f} {result.memory_used_gb:<10.1f} "
                      f"{result.throughput_pages_per_sec:<12.2f} {status}")
            else:
                print(f"{description:<15} {result.batch_size:<8} {result.workers:<8} "
                      f"{'N/A':<10} {'N/A':<10} {'N/A':<12} {status}")

        # Find best configuration
        successful = [r for r in self.results if r.success]
        if successful:
            best = min(successful, key=lambda x: x.duration_seconds)
            print(f"\n{'='*80}")
            print("Best Configuration:")
            print(f"  Batch Size: {best.batch_size}")
            print(f"  Workers: {best.workers}")
            print(f"  Duration: {best.duration_seconds:.1f}s")
            print(f"  Throughput: {best.throughput_pages_per_sec:.2f} pages/s")
            print(f"  Memory Used: {best.memory_used_gb:.1f} GB")
            print(f"{'='*80}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="AMD CPU Performance Benchmark for PDF2MD"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        required=True,
        help="Path to PDF file for benchmarking"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick benchmark (3 configurations only)"
    )
    parser.add_argument(
        "--config",
        type=str,
        nargs="+",
        help="Custom configurations: 'batch_size,workers' (e.g., '32,16 24,16')"
    )

    args = parser.parse_args()

    # Validate PDF path
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    # Create benchmark suite
    benchmark = CPUBenchmark(pdf_path)

    # Parse custom configs if provided
    if args.config:
        configs = []
        for config_str in args.config:
            try:
                batch, workers = config_str.split(",")
                configs.append((int(batch), int(workers), "Custom"))
            except ValueError:
                print(f"Error: Invalid config format: {config_str}")
                print("Expected format: batch_size,workers (e.g., '32,16')")
                sys.exit(1)

        benchmark.run_full_benchmark(configs)
    elif args.quick:
        benchmark.run_quick_benchmark()
    else:
        benchmark.run_full_benchmark()


if __name__ == "__main__":
    main()
