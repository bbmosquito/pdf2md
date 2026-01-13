#!/usr/bin/env python3
"""
测试进度条实际行为
模拟批处理的进度更新
"""

import sys
import time
from pathlib import Path

# Ensure UTF-8 encoding
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

console = Console()


def test_progress_updates():
    """测试进度条是否会更新"""
    console.print("\n[bold cyan]测试1: 模拟批处理进度更新[/bold cyan]\n")

    total_tasks = 5
    completed_count = [0]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[bold cyan]{task.completed}[/bold cyan]/{task.total}"),
        console=console
    ) as progress:

        task = progress.add_task(
            "Converting PDFs...",
            total=total_tasks
        )

        def progress_callback(current: int, total: int, message: str):
            # Update progress bar manually when callback is invoked
            new_completed = current - completed_count[0]
            console.print(f"[dim]回调被调用: current={current}, completed_count[0]={completed_count[0]}, new_completed={new_completed}[/dim]")
            if new_completed > 0:
                progress.update(task, advance=new_completed)
                completed_count[0] = current

        # 模拟批处理调用回调
        for i in range(1, total_tasks + 1):
            time.sleep(0.5)
            console.print(f"[yellow]处理任务 {i}/{total_tasks}...[/yellow]")
            progress_callback(i, total_tasks, f"Converted document_{i}.pdf")

    console.print("\n[green]OK 测试完成[/green]\n")
    return True


def test_direct_update():
    """测试直接更新进度条"""
    console.print("[bold cyan]测试2: 直接更新进度条[/bold cyan]\n")

    total_tasks = 5

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[bold cyan]{task.completed}[/bold cyan]/{task.total}"),
        console=console
    ) as progress:

        task = progress.add_task(
            "Converting PDFs...",
            total=total_tasks
        )

        for i in range(total_tasks):
            time.sleep(0.5)
            progress.update(task, advance=1)
            console.print(f"[yellow]已更新: {i+1}/{total_tasks}[/yellow]")

    console.print("\n[green]OK 测试完成[/green]\n")
    return True


def main():
    console.print("\n")
    console.print("╔══════════════════════════════════════════════════════════════╗")
    console.print("║                                                              ║")
    console.print("║     PDF2MD 进度条实际行为测试                                  ║")
    console.print("║                                                              ║")
    console.print("╚══════════════════════════════════════════════════════════════╝")
    console.print("\n")

    # 运行测试
    test_progress_updates()
    time.sleep(1)

    test_direct_update()

    console.print("[bold green]测试完成！请观察进度条是否正确更新。[/bold green]\n")


if __name__ == "__main__":
    main()
