#!/usr/bin/env python3
"""
使用真实的批处理代码测试进度条
验证日志干扰是否已修复
"""

import sys
import time
import logging
from pathlib import Path

# Ensure UTF-8 encoding
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# Setup logging to simulate real scenario
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

console = Console()


def simulate_docling_logging():
    """模拟 docling 的日志输出"""
    docling_logger = logging.getLogger('docling')
    rapidocr_logger = logging.getLogger('RapidOCR')

    # 模拟各种日志
    docling_logger.info("Going to convert document batch...")
    docling_logger.info("Initializing pipeline for StandardPdfPipeline")
    docling_logger.info("Loading plugin 'docling_defaults'")
    docling_logger.info("Registered ocr engines: ['auto', 'easyocr', ...]")

    rapidocr_logger.info("[RapidOCR] Using engine_name: torch")
    rapidocr_logger.info("[RapidOCR] Using CPU device")


def test_with_logging_noise():
    """测试在有日志干扰的情况下进度条是否可见"""
    console.print("\n[bold cyan]测试: 进度条在日志干扰下的可见性[/bold cyan]\n")

    tasks = [
        "document1.pdf",
        "document2.pdf",
        "document3.pdf",
        "document4.pdf",
        "document5.pdf",
    ]

    total_tasks = len(tasks)
    completed_count = [0]

    console.print(f"[cyan]准备处理 {total_tasks} 个任务...[/cyan]\n")

    # 启用日志干扰测试
    console.print("[yellow]启用详细日志输出 (模拟真实场景)...[/yellow]\n")

    # Reduce log noise during batch processing
    docling_logger = logging.getLogger('docling')
    rapidocr_logger = logging.getLogger('RapidOCR')
    old_docling_level = docling_logger.level
    old_rapidocr_level = rapidocr_logger.level

    try:
        # 临时降低日志级别
        docling_logger.setLevel(logging.WARNING)
        rapidocr_logger.setLevel(logging.WARNING)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[bold cyan]{task.completed}[/bold cyan]/{task.total}"),
            console=console,
            refresh_per_second=10
        ) as progress:

            task = progress.add_task(
                "Converting PDFs...",
                total=total_tasks
            )

            def progress_callback(current: int, total: int, message: str):
                new_completed = current - completed_count[0]
                if new_completed > 0:
                    progress.update(task, advance=new_completed)
                    completed_count[0] = current

            # 模拟批处理
            for i, task_name in enumerate(tasks, 1):
                # 模拟 docling 日志输出（这些会被抑制）
                simulate_docling_logging()

                time.sleep(1.0)  # 模拟转换耗时

                # 输出进度更新
                console.print(f"[green]✓ 完成: {task_name}[/green]")

                progress_callback(i, total_tasks, f"Converted {task_name}")

    finally:
        # 恢复日志级别
        docling_logger.setLevel(old_docling_level)
        rapidocr_logger.setLevel(old_rapidocr_level)

    console.print("\n[green]✓ 测试完成[/green]\n")
    console.print("[yellow]请检查上面的输出：[/yellow]")
    console.print("1. 是否看到清晰的进度条（而不是被日志淹没）")
    console.print("2. 进度条是否显示 'Converting PDFs... X/5'")
    console.print("3. 是否有进度百分比和进度条图形\n")


def test_without_logging_fix():
    """对比测试：不降低日志级别时的情况"""
    console.print("\n[bold cyan]对比测试: 不降低日志级别时的情况[/bold cyan]\n")

    console.print("[yellow]注意：这个测试会显示大量日志，模拟未修复的场景[/yellow]\n")
    time.sleep(2)

    total_tasks = 3
    completed_count = [0]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[bold cyan]{task.completed}[/bold cyan]/{task.total}"),
        console=console,
        refresh_per_second=10
    ) as progress:

        task = progress.add_task(
            "Converting PDFs...",
            total=total_tasks
        )

        for i in range(1, total_tasks + 1):
            # 不降低日志级别，模拟日志干扰
            simulate_docling_logging()

            time.sleep(0.5)

            new_completed = i - completed_count[0]
            if new_completed > 0:
                progress.update(task, advance=new_completed)
                completed_count[0] = i

    console.print("\n[dim]对比测试完成 - 注意上面的日志是否淹没了进度条[/dim]\n")


def main():
    console.print("\n")
    console.print("╔══════════════════════════════════════════════════════════════╗")
    console.print("║                                                              ║")
    console.print("║     PDF2MD 真实批处理进度条测试 (含日志干扰)                     ║")
    console.print("║                                                              ║")
    console.print("╚══════════════════════════════════════════════════════════════╝")
    console.print("\n")

    # 测试修复后的版本
    test_with_logging_noise()

    time.sleep(2)

    # 对比测试
    console.print("\n" + "="*70 + "\n")
    test_without_logging_fix()

    console.print("[bold green]所有测试完成！[/bold green]")
    console.print("\n[cyan]总结：[/cyan]")
    console.print("✓ 修复后的版本应该显示清晰的进度条")
    console.print("✓ 日志干扰被抑制到 WARNING 级别")
    console.print("✓ 进度条更新可见且清晰\n")


if __name__ == "__main__":
    main()
