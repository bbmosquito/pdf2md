"""
Command Line Interface for PDF2MD.

Provides CLI commands for converting PDFs to Markdown.
"""

import sys
import click
from pathlib import Path
from typing import Optional, List
import logging

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich import print as rprint

from core.converter import DoclingConverter, ConversionConfig, is_docling_available, install_docling_instructions
from batch.task_queue import TaskQueue, TaskStatus
from batch.batch_processor import BatchProcessor
from utils.logger import setup_logging, get_logger
from utils.config import load_config, Config
from core.cpu_optimizer import AMDCPUOptimizer

console = Console()
logger = None


def print_banner():
    """Print application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     [bold cyan]PDF2MD[/bold cyan] - Large PDF to Markdown Converter     ║
║                                                              ║
║     Optimized for files [yellow]>200MB[/yellow] with memory control      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    rprint(banner)


def check_dependencies() -> bool:
    """Check if required dependencies are installed."""
    if not is_docling_available():
        console.print("[red]Error: Docling is not installed[/red]")
        console.print(install_docling_instructions())
        return False
    return True


@click.group()
@click.version_option(version="0.1.0", prog_name="pdf2md")
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
def main(config: Optional[str], verbose: bool, quiet: bool):
    """
    PDF2MD - Convert large PDF files to Markdown format.

    Optimized for handling scanned PDFs >200MB with memory-efficient processing.
    """
    global logger

    # Load configuration
    cfg = load_config(config)

    # Set log level
    if verbose:
        cfg.logging.level = "DEBUG"
    elif quiet:
        cfg.logging.level = "ERROR"

    logger = setup_logging(
        level=cfg.logging.level,
        log_file=cfg.logging.file,
        console=not quiet
    )

    get_logger(__name__).info("PDF2MD initialized")


@main.command()
@click.argument("pdf", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output directory (default: same as PDF with _md suffix)"
)
@click.option(
    "--workers", "-w",
    type=int,
    default=None,
    help="Number of parallel workers (default: auto-detect)"
)
@click.option(
    "--ocr/--no-ocr",
    default=True,
    help="Enable/disable OCR for scanned pages"
)
@click.option(
    "--dpi",
    type=int,
    default=200,
    help="DPI for image rendering (default: 200)"
)
@click.option(
    "--gpu/--no-gpu",
    default=True,
    help="Enable/disable GPU acceleration (default: auto-detect)"
)
@click.option(
    "--device",
    type=click.Choice(["auto", "cuda", "mps", "cpu"]),
    default="auto",
    help="Accelerator device (default: auto)"
)
@click.option(
    "--batch-size",
    type=int,
    default=None,
    help="OCR and layout batch size (default: auto-detect)"
)
def convert(
    pdf: str,
    output: Optional[str],
    workers: int,
    ocr: bool,
    dpi: int,
    gpu: bool,
    device: str,
    batch_size: int
):
    """
    Convert a PDF file to Markdown.

    Examples:

        # Basic conversion (auto-detect optimal settings)
        pdf2md convert document.pdf

        # Specify output directory
        pdf2md convert document.pdf -o ./output

        # Disable OCR
        pdf2md convert document.pdf --no-ocr

        # High DPI for better quality
        pdf2md convert document.pdf --dpi 300

        # Force CPU mode (no GPU)
        pdf2md convert document.pdf --no-gpu

        # Use specific device
        pdf2md convert document.pdf --device cuda

        # Custom batch size
        pdf2md convert document.pdf --batch-size 32
    """
    if not check_dependencies():
        sys.exit(1)

    print_banner()

    # Auto-detect optimal workers and batch size if not specified
    optimizer_config = None
    if workers is None or batch_size is None:
        import psutil

        # Use intelligent CPU optimizer for configuration
        optimizer = AMDCPUOptimizer()

        if workers is None:
            workers = optimizer.calculate_optimal_workers()
            console.print(f"[cyan]Auto-detected workers:[/cyan] {workers}")

        if batch_size is None:
            optimizer_config = optimizer.get_optimal_config(enable_gpu=gpu)
            batch_size = optimizer_config.ocr_batch_size
            console.print(f"[cyan]Auto-detected batch size:[/cyan] {batch_size}")
            console.print(f"[dim]  ({optimizer.system.physical_cores} cores, "
                        f"{optimizer.system.available_memory_gb:.1f}GB available, "
                        f"GPU={'enabled' if gpu else 'disabled'})[/dim]")

    # Create converter configuration
    config = ConversionConfig(
        ocr_enabled=ocr,
        dpi=dpi,
        max_workers=workers,
        enable_gpu=gpu,
        accelerator_device=device,
        ocr_batch_size=batch_size,
        layout_batch_size=batch_size,
        table_batch_size=optimizer_config.table_batch_size if optimizer_config else batch_size // 4,
        num_threads=optimizer_config.num_threads if optimizer_config else None
    )

    # Create converter
    try:
        converter = DoclingConverter(config)
    except Exception as e:
        console.print(f"[red]Failed to initialize converter: {e}[/red]")
        sys.exit(1)

    # Progress tracking
    pdf_path = Path(pdf)

    with console.status(f"[bold green]Converting {pdf_path.name}...") as status:
        def progress_callback(progress: float, message: str):
            status.update(f"[bold green]{message}[/bold green] ({progress*100:.0f}%)")

        result = converter.convert(
            pdf_path,
            output,
            progress_callback=progress_callback
        )

    # Display result
    if result.success:
        console.print(Panel.fit(
            f"[bold green][+] Conversion successful![/bold green]\n\n"
            f"Source: {result.source_path}\n"
            f"Output: {result.output_path}\n"
            f"Pages: {result.pages_converted}/{result.total_pages}\n"
            f"Images: {result.images_extracted}\n"
            f"Duration: {result.duration_seconds:.1f}s",
            title="Result",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            f"[bold red][-] Conversion failed[/bold red]\n\n"
            f"Error: {result.error_message}",
            title="Error",
            border_style="red"
        ))
        sys.exit(1)


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output directory for converted files"
)
@click.option(
    "--pattern",
    type=str,
    default="*.pdf",
    help="Glob pattern for PDF files (default: *.pdf)"
)
@click.option(
    "--recursive", "-r",
    is_flag=True,
    help="Search recursively in subdirectories"
)
@click.option(
    "--workers", "-w",
    type=int,
    default=4,
    help="Number of parallel workers"
)
@click.option(
    "--ocr/--no-ocr",
    default=True,
    help="Enable/disable OCR"
)
def batch(
    directory: str,
    output: Optional[str],
    pattern: str,
    recursive: bool,
    workers: int,
    ocr: bool
):
    """
    Batch convert all PDFs in a directory.

    Examples:

        # Convert all PDFs in current directory
        pdf2md batch .

        # Convert recursively with custom output
        pdf2md batch ./pdfs -o ./markdown -r

        # Only convert specific files
        pdf2md batch . --pattern "chapter_*.pdf"
    """
    if not check_dependencies():
        sys.exit(1)

    print_banner()

    # Create converter
    config = ConversionConfig(
        ocr_enabled=ocr,
        max_workers=workers
    )

    try:
        converter = DoclingConverter(config)
    except Exception as e:
        console.print(f"[red]Failed to initialize converter: {e}[/red]")
        sys.exit(1)

    # Create task queue
    queue = TaskQueue()
    queue.add_from_directory(
        directory,
        pattern=pattern,
        recursive=recursive,
        output_dir=output
    )

    if queue.pending_count == 0:
        console.print(f"[yellow]No PDF files found in {directory}[/yellow]")
        sys.exit(0)

    console.print(f"[cyan]Found {queue.pending_count} PDF file(s) to convert[/cyan]")

    # Create processor
    processor = BatchProcessor(converter, max_workers=workers)

    # Reduce log noise during batch processing to keep progress bar visible
    import logging
    docling_logger = logging.getLogger('docling')
    rapidocr_logger = logging.getLogger('RapidOCR')
    old_docling_level = docling_logger.level
    old_rapidocr_level = rapidocr_logger.level
    docling_logger.setLevel(logging.WARNING)
    rapidocr_logger.setLevel(logging.WARNING)

    try:
        # Process with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[bold cyan]{task.completed}[/bold cyan]/{task.total}"),
            console=console,
            refresh_per_second=10  # Control refresh rate
        ) as progress:
            task = progress.add_task(
                "Converting PDFs...",
                total=queue.pending_count
            )

            completed_count = [0]  # Use list to allow modification in closure

            def progress_callback(current: int, total: int, message: str):
                # Update progress bar manually when callback is invoked
                new_completed = current - completed_count[0]
                if new_completed > 0:
                    progress.update(task, advance=new_completed)
                    completed_count[0] = current

            results = processor.process(queue, progress_callback)

    finally:
        # Restore log levels
        docling_logger.setLevel(old_docling_level)
        rapidocr_logger.setLevel(old_rapidocr_level)

    # Display summary
    summary = processor.get_summary()

    console.print("\n")
    console.print(Panel.fit(
        f"[bold]Batch Conversion Complete[/bold]\n\n"
        f"Total: {summary['total']}\n"
        f"[green]Successful: {summary['successful']}[/green]\n"
        f"[red]Failed: {summary['failed']}[/red]\n"
        f"Total Pages: {summary['total_pages']}\n"
        f"Total Images: {summary['total_images']}\n"
        f"Total Duration: {summary['total_duration']:.1f}s",
        title="Summary",
        border_style="cyan"
    ))

    # Show failed conversions
    failed_results = [r for r in results if not r.success]
    if failed_results:
        console.print("\n[red]Failed conversions:[/red]")
        for result in failed_results:
            # Ensure proper encoding for Chinese filenames
            try:
                filename = str(result.source_path.name)
            except:
                filename = result.source_path.name.encode('utf-8', errors='ignore').decode('utf-8')
            console.print(f"  • {filename}: {result.error_message}")


@main.command()
@click.argument("pdfs", nargs=-1, type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output directory"
)
@click.option(
    "--workers", "-w",
    type=int,
    default=4,
    help="Number of parallel workers"
)
@click.option(
    "--ocr/--no-ocr",
    default=True,
    help="Enable/disable OCR"
)
def multiple(
    pdfs: tuple,
    output: Optional[str],
    workers: int,
    ocr: bool
):
    """
    Convert multiple specific PDF files.

    Example:

        pdf2md multiple file1.pdf file2.pdf file3.pdf -o ./output
    """
    if not pdfs:
        console.print("[yellow]No PDF files specified[/yellow]")
        console.print("Usage: pdf2md multiple FILE1 [FILE2 ...] [OPTIONS]")
        sys.exit(1)

    if not check_dependencies():
        sys.exit(1)

    print_banner()

    # Create converter
    config = ConversionConfig(
        ocr_enabled=ocr,
        max_workers=workers
    )

    try:
        converter = DoclingConverter(config)
    except Exception as e:
        console.print(f"[red]Failed to initialize converter: {e}[/red]")
        sys.exit(1)

    # Create task queue
    queue = TaskQueue()
    queue.add_many(list(pdfs), output_dir=output)

    console.print(f"[cyan]Converting {queue.pending_count} PDF file(s)[/cyan]")

    # Process
    processor = BatchProcessor(converter, max_workers=workers)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[bold cyan]{task.fields[current]}[/bold cyan]/{task.fields[total]}"),
        console=console
    ) as progress:

        task = progress.add_task(
            "Converting...",
            total=queue.pending_count,
            current=0
        )

        def progress_callback(current: int, total: int, message: str):
            progress.update(task, advance=1, current=current)

        results = processor.process(queue, progress_callback)

    # Summary
    summary = processor.get_summary()
    console.print(Panel.fit(
        f"[green]Successful: {summary['successful']}[/green] | "
        f"[red]Failed: {summary['failed']}[/red] | "
        f"Duration: {summary['total_duration']:.1f}s",
        title="Result"
    ))


@main.command()
def info():
    """Show system and dependency information."""
    print_banner()

    table = Table(title="System Information")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    # Python version
    import sys
    table.add_row(
        "Python",
        "[green]OK[/green]",
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    # Docling
    if is_docling_available():
        try:
            import docling
            table.add_row("Docling", "[green]OK[/green]", getattr(docling, "__version__", "unknown"))
        except:
            table.add_row("Docling", "[green]OK[/green]", "installed")
    else:
        table.add_row("Docling", "[red]Not installed[/red]", install_docling_instructions())

    # Platform
    import platform
    table.add_row(
        "Platform",
        "[green]OK[/green]",
        f"{platform.system()} {platform.machine()}"
    )

    console.print(table)


def main_entry():
    """Entry point for the CLI."""
    main()


if __name__ == "__main__":
    main_entry()
