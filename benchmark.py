"""
Performance Benchmark Tool for PDF2MD.

Tests and compares performance with different settings.
"""

import sys
import time
import psutil
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from core.converter import DoclingConverter, ConversionConfig, ACCELERATOR_AVAILABLE
from utils.system_detector import SystemDetector, get_system_detector
from utils.logger import setup_logging

console = Console()


class PerformanceBenchmark:
    """
    Benchmark PDF conversion performance.

    Tests different configurations and measures:
    - Conversion time
    - Memory usage
    - Pages per second
    - GPU utilization
    """

    def __init__(self, pdf_path: Path):
        """
        Initialize benchmark.

        Args:
            pdf_path: Path to PDF file for testing
        """
        self.pdf_path = pdf_path
        self.detector = get_system_detector()
        self.system_caps = self.detector.detect()

        # Setup logging
        setup_logging(level="INFO", log_file="benchmark.log", console=False)
        self.logger = logging.getLogger(__name__)

    def run_benchmark(self) -> Dict[str, Any]:
        """
        Run comprehensive performance benchmark.

        Returns:
            Dictionary with benchmark results
        """
        console.print("\n[bold cyan]PDF2MD Performance Benchmark[/bold cyan]\n")

        # Print system info
        self.detector.print_system_info()

        # Check PDF
        if not self.pdf_path.exists():
            console.print(f"[red]Error: PDF file not found: {self.pdf_path}[/red]")
            return {}

        # Get PDF info
        try:
            from core.pdf_reader import PDFReader
            with PDFReader(self.pdf_path) as reader:
                info = reader.get_info()

            console.print(Panel.fit(
                f"[bold]Test File:[/bold] {self.pdf_path.name}\n"
                f"[bold]Size:[/bold] {info.file_size_mb:.1f} MB\n"
                f"[bold]Pages:[/bold] {info.total_pages}\n"
                f"[bold]Type:[/bold] {'Large file' if info.is_large_file else 'Normal file'}",
                title="Test Document",
                border_style="cyan"
            ))
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read PDF info: {e}[/yellow]")

        # Run tests
        results = {
            "system": self.system_caps,
            "pdf_info": {
                "name": self.pdf_path.name,
                "size_mb": info.file_size_mb,
                "pages": info.total_pages
            },
            "tests": []
        }

        # Test 1: Default settings (CPU, no GPU)
        console.print("\n[bold]Test 1: Default CPU Configuration[/bold]")
        console.print("[dim]Baseline performance without GPU acceleration[/dim]\n")

        test1_result = self._run_test(
            name="CPU (No GPU)",
            config=ConversionConfig(
                enable_gpu=False,
                max_workers=4,
                ocr_batch_size=4,
                layout_batch_size=4
            )
        )
        results["tests"].append(test1_result)

        # Test 2: Optimized CPU (more workers, larger batches)
        console.print("\n[bold]Test 2: Optimized CPU Configuration[/bold]")
        console.print("[dim]Higher worker count and batch sizes[/dim]\n")

        test2_result = self._run_test(
            name="CPU (Optimized)",
            config=ConversionConfig(
                enable_gpu=False,
                max_workers=self.system_caps.get_optimal_workers(),
                ocr_batch_size=self.system_caps.get_optimal_batch_size(),
                layout_batch_size=self.system_caps.get_optimal_batch_size(),
                process_chunk_size=self.system_caps.get_recommended_chunk_size()
            )
        )
        results["tests"].append(test2_result)

        # Test 3: GPU accelerated (if available)
        if ACCELERATOR_AVAILABLE and self.system_caps.gpu.vendor != "none":
            console.print("\n[bold]Test 3: GPU Accelerated Configuration[/bold]")
            console.print("[dim]Using GPU with optimized batch sizes[/dim]\n")

            test3_result = self._run_test(
                name="GPU Accelerated",
                config=ConversionConfig(
                    enable_gpu=True,
                    accelerator_device="auto",
                    max_workers=self.system_caps.get_optimal_workers(),
                    num_threads=self.system_caps.cpu.cores_physical,
                    ocr_batch_size=64,  # Large batch for GPU
                    layout_batch_size=64,
                    table_batch_size=8,
                    process_chunk_size=self.system_caps.get_recommended_chunk_size()
                )
            )
            results["tests"].append(test3_result)
        else:
            console.print("\n[yellow]GPU acceleration not available, skipping GPU test[/yellow]")

        # Print summary
        self._print_summary(results)

        return results

    def _run_test(self, name: str, config: ConversionConfig) -> Dict[str, Any]:
        """
        Run a single benchmark test.

        Args:
            name: Test name
            config: Conversion configuration

        Returns:
            Test results dictionary
        """
        try:
            # Create converter
            converter = DoclingConverter(config)

            # Measure memory before
            process = psutil.Process()
            mem_before = process.memory_info().rss / (1024 * 1024)

            # Time the conversion
            start_time = time.time()

            result = converter.convert(
                self.pdf_path,
                progress_callback=lambda p, m: None  # No progress for benchmark
            )

            elapsed = time.time() - start_time

            # Measure memory after
            mem_after = process.memory_info().rss / (1024 * 1024)
            mem_peak = max(mem_before, mem_after)
            mem_used = mem_after - mem_before

            # Calculate metrics
            if result.success:
                pages_per_sec = result.pages_converted / elapsed if elapsed > 0 else 0
            else:
                pages_per_sec = 0

            test_result = {
                "name": name,
                "success": result.success,
                "duration_seconds": elapsed,
                "pages_converted": result.pages_converted,
                "pages_per_second": pages_per_sec,
                "memory_mb": {
                    "before": mem_before,
                    "after": mem_after,
                    "used": mem_used,
                    "peak": mem_peak
                },
                "config": {
                    "enable_gpu": config.enable_gpu,
                    "max_workers": config.max_workers,
                    "ocr_batch_size": config.ocr_batch_size,
                    "layout_batch_size": config.layout_batch_size,
                    "num_threads": config.num_threads
                },
                "error": result.error_message if not result.success else None
            }

            # Print result
            if result.success:
                console.print(f"[green]✓[/green] {name}")
                console.print(f"  Time: {elapsed:.1f}s")
                console.print(f"  Speed: {pages_per_sec:.2f} pages/sec")
                console.print(f"  Memory: {mem_used:.0f} MB")
            else:
                console.print(f"[red]✗[/red] {name}")
                console.print(f"  Error: {result.error_message}")

            return test_result

        except Exception as e:
            console.print(f"[red]✗[/red] {name}")
            console.print(f"  Exception: {e}")

            return {
                "name": name,
                "success": False,
                "error": str(e)
            }

    def _print_summary(self, results: Dict[str, Any]):
        """Print benchmark summary table."""
        if not results["tests"]:
            return

        console.print("\n[bold]Benchmark Summary[/bold]\n")

        table = Table(title="Performance Comparison")
        table.add_column("Configuration", style="cyan")
        table.add_column("Time (s)", justify="right")
        table.add_column("Pages/s", justify="right")
        table.add_column("Memory (MB)", justify="right")
        table.add_column("Speedup", justify="right")

        baseline_time = None
        baseline_pages_per_sec = None

        for test in results["tests"]:
            if not test["success"]:
                continue

            if baseline_time is None:
                baseline_time = test["duration_seconds"]
                baseline_pages_per_sec = test["pages_per_second"]
                speedup = "1.00x (baseline)"
            else:
                speedup_val = baseline_time / test["duration_seconds"]
                speedup = f"{speedup_val:.2f}x"

            table.add_row(
                test["name"],
                f"{test['duration_seconds']:.1f}",
                f"{test['pages_per_second']:.2f}",
                f"{test['memory_mb']['used']:.0f}",
                speedup
            )

        console.print(table)

        # Print recommendations
        console.print("\n[bold cyan]Recommendations[/bold cyan]\n")

        if len(results["tests"]) >= 2:
            cpu_test = results["tests"][0]
            opt_cpu_test = results["tests"][1]

            if cpu_test["success"] and opt_cpu_test["success"]:
                speedup = cpu_test["duration_seconds"] / opt_cpu_test["duration_seconds"]
                console.print(f"• Optimized CPU settings provide {speedup:.2f}x speedup over baseline")

        if len(results["tests"]) >= 3:
            gpu_test = results["tests"][2]
            if gpu_test["success"]:
                speedup = baseline_time / gpu_test["duration_seconds"]
                console.print(f"• GPU acceleration provides {speedup:.2f}x speedup over baseline")

        console.print(f"\n[green]✓ Best configuration:[/green] {self._get_best_config(results)}")

    def _get_best_config(self, results: Dict[str, Any]) -> str:
        """Get name of best performing configuration."""
        best_time = float('inf')
        best_name = "None"

        for test in results["tests"]:
            if test["success"] and test["duration_seconds"] < best_time:
                best_time = test["duration_seconds"]
                best_name = test["name"]

        return best_name


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="PDF2MD Performance Benchmark"
    )
    parser.add_argument(
        "pdf",
        type=str,
        help="Path to PDF file for benchmarking"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Save results to JSON file"
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        console.print(f"[red]Error: PDF file not found: {pdf_path}[/red]")
        sys.exit(1)

    # Run benchmark
    benchmark = PerformanceBenchmark(pdf_path)
    results = benchmark.run_benchmark()

    # Save to JSON if requested
    if args.output:
        import json
        from dataclasses import asdict

        # Convert dataclasses to dicts
        def convert_to_dict(obj):
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            elif isinstance(obj, list):
                return [convert_to_dict(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_to_dict(v) for k, v in obj.items()}
            else:
                return obj

        results_dict = convert_to_dict(results)

        with open(args.output, 'w') as f:
            json.dump(results_dict, f, indent=2)

        console.print(f"\n[cyan]Results saved to:[/cyan] {args.output}")


if __name__ == "__main__":
    main()
