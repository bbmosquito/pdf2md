#!/usr/bin/env python3
"""
模拟真实的批处理场景
测试进度条在实际转换中的表现
"""

import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

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


def simulate_conversion(task_name: str, duration: float):
    """模拟一个 PDF 转换任务"""
    time.sleep(duration)
    return {"name": task_name, "success": True, "pages": 10}


def test_real_batch_processing():
    """测试真实的批处理场景"""
    console.print("\n[bold cyan]真实批处理场景测试[/bold cyan]\n")

    # 模拟任务队列
    tasks = [
        "document1.pdf",
        "document2.pdf",
        "document3.pdf",
        "document4.pdf",
        "document5.pdf",
    ]

    total_tasks = len(tasks)
    results = []
    lock = Lock()
    completed = 0

    console.print(f"[cyan]准备处理 {total_tasks} 个任务...[/cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[bold cyan]{task.completed}[/bold cyan]/{task.total}"),
        console=console,
        refresh_per_second=10  # 控制刷新率
    ) as progress:

        task = progress.add_task(
            "Converting PDFs...",
            total=total_tasks
        )

        completed_count = [0]

        def progress_callback(current: int, total: int, message: str):
            """进度回调函数"""
            new_completed = current - completed_count[0]
            if new_completed > 0:
                progress.update(task, advance=new_completed)
                completed_count[0] = current
                console.print(f"[dim]进度更新: {current}/{total} - {message}[/dim]")

        # 使用线程池模拟批处理
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 提交所有任务
            futures = {executor.submit(simulate_conversion, task_name, 1.5): task_name
                      for task_name in tasks}

            console.print("[yellow]开始并行处理 (2个worker)...[/yellow]\n")

            # 处理完成的任务
            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result = future.result()
                    with lock:
                        results.append(result)
                        completed += 1

                    console.print(f"[green]✓ 完成: {task_name}[/green]")

                    if progress_callback:
                        message = f"Converted {task_name}"
                        if result["success"]:
                            message += f" ({result['pages']} pages)"
                        progress_callback(completed, total_tasks, message)

                except Exception as e:
                    console.print(f"[red]✗ 失败: {task_name} - {e}[/red]")
                    with lock:
                        completed += 1

                    if progress_callback:
                        progress_callback(completed, total_tasks, f"Error: {task_name}")

    # 显示汇总
    console.print("\n")
    console.print("╔══════════════════════════════════════════════════════════════╗")
    console.print("║                        处理结果                                 ║")
    console.print("╚══════════════════════════════════════════════════════════════╝\n")

    successful = len([r for r in results if r["success"]])
    console.print(f"总计: {len(results)}")
    console.print(f"[green]成功: {successful}[/green]")
    console.print(f"[red]失败: {len(results) - successful}[/red]\n")

    return True


def test_slow_progress():
    """测试慢速进度更新，便于观察"""
    console.print("\n[bold cyan]慢速进度更新测试 (便于观察)[/bold cyan]\n")

    total = 10

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[bold cyan]{task.completed}[/bold cyan]/{task.total}"),
        console=console,
        refresh_per_second=4  # 降低刷新率以便观察
    ) as progress:

        task = progress.add_task("Processing...", total=total)

        for i in range(total):
            time.sleep(0.8)  # 每次等待0.8秒
            progress.update(task, advance=1)
            console.print(f"[cyan]进度: {i+1}/{total}[/cyan]")

    console.print("\n[green]测试完成[/green]\n")
    return True


def main():
    console.print("\n")
    console.print("╔══════════════════════════════════════════════════════════════╗")
    console.print("║                                                              ║")
    console.print("║     PDF2MD 真实批处理进度条测试                                ║")
    console.print("║                                                              ║")
    console.print("╚══════════════════════════════════════════════════════════════╝")
    console.print("\n")

    # 运行测试
    test_slow_progress()
    time.sleep(1)

    test_real_batch_processing()

    console.print("[bold green]所有测试完成！[/bold green]")
    console.print("\n[yellow]请观察上面的输出：[/yellow]")
    console.print("1. 进度条是否从 0% 逐步更新到 100%")
    console.print("2. 进度计数是否正确 (如 1/5, 2/5, 3/5...)")
    console.print("3. 进度条文本是否显示完整\n")


if __name__ == "__main__":
    main()
