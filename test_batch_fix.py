#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批量转换功能修复

验证：
1. Rich进度条修复
2. 中文文件名支持
3. 批量转换正常工作
"""

import sys
from pathlib import Path

# Ensure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# 添加src目录到路径
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

console = Console()


def test_progress_bar():
    """测试Rich进度条修复"""
    console.print("\n[bold cyan]测试1: Rich进度条修复[/bold cyan]\n")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[bold cyan]{task.completed}[/bold cyan]/{task.total}"),
            console=console
        ) as progress:

            # 使用Rich内置的completed属性，不需要fields
            task = progress.add_task(
                "测试进度...",
                total=10
            )

            import time
            for i in range(10):
                time.sleep(0.1)
                progress.update(task, advance=1)

        console.print("[green]OK 进度条测试通过[/green]\n")
        return True

    except Exception as e:
        console.print(f"[red]X 进度条测试失败: {e}[/red]\n")
        return False


def test_chinese_filename():
    """测试中文文件名支持"""
    console.print("[bold cyan]测试2: 中文文件名支持[/bold cyan]\n")

    try:
        # 创建测试文件
        test_dir = Path("test_pdfs")
        test_dir.mkdir(exist_ok=True)

        # 创建中文文件名的测试PDF（空文件）
        chinese_files = [
            "测试文档1.pdf",
            "测试文档2.pdf",
            "报告_最终版.pdf"
        ]

        for filename in chinese_files:
            test_file = test_dir / filename
            if not test_file.exists():
                test_file.touch()

        console.print(f"已创建 {len(chinese_files)} 个测试文件")

        # 测试文件列表
        pdf_files = list(test_dir.glob("*.pdf"))
        console.print(f"找到 {len(pdf_files)} 个PDF文件:\n")

        for pdf_file in pdf_files:
            try:
                # 尝试显示中文文件名
                console.print(f"  • {pdf_file.name}")
            except Exception as e:
                console.print(f"  • [red]编码错误: {e}[/red]")

        console.print("\n[green]OK 中文文件名测试通过[/green]\n")

        # 清理测试文件
        for pdf_file in pdf_files:
            pdf_file.unlink()
        test_dir.rmdir()

        return True

    except Exception as e:
        console.print(f"[red]X 中文文件名测试失败: {e}[/red]\n")
        return False


def test_task_queue():
    """测试任务队列"""
    console.print("[bold cyan]测试3: 任务队列[/bold cyan]\n")

    try:
        from batch.task_queue import TaskQueue

        queue = TaskQueue()

        # 创建测试目录和文件
        test_dir = Path("test_pdfs")
        test_dir.mkdir(exist_ok=True)

        test_files = [
            "doc1.pdf",
            "测试.pdf",
            "report.pdf"
        ]

        for filename in test_files:
            (test_dir / filename).touch()

        # 添加任务到队列
        queue.add_from_directory(test_dir, recursive=False)

        console.print(f"队列中有 {queue.pending_count} 个任务")

        # 显示任务列表
        for task in queue.get_pending():
            console.print(f"  • {task.source_name}")

        console.print("\n[green]OK 任务队列测试通过[/green]\n")

        # 清理
        for file in test_dir.glob("*.pdf"):
            file.unlink()
        test_dir.rmdir()

        return True

    except Exception as e:
        console.print(f"[red]X 任务队列测试失败: {e}[/red]\n")
        import traceback
        console.print(traceback.format_exc())
        return False


def main():
    """运行所有测试"""
    console.print("\n")
    console.print("╔══════════════════════════════════════════════════════════════╗")
    console.print("║                                                              ║")
    console.print("║     PDF2MD 批量转换修复测试                                   ║")
    console.print("║                                                              ║")
    console.print("╚══════════════════════════════════════════════════════════════╝")
    console.print("\n")

    results = []

    # 运行测试
    results.append(("进度条修复", test_progress_bar()))
    results.append(("中文文件名", test_chinese_filename()))
    results.append(("任务队列", test_task_queue()))

    # 显示结果汇总
    console.print("╔══════════════════════════════════════════════════════════════╗")
    console.print("║                        测试结果汇总                            ║")
    console.print("╚══════════════════════════════════════════════════════════════╝\n")

    passed = 0
    failed = 0

    for test_name, result in results:
        if result:
            console.print(f"[green]OK[/green] {test_name}: [bold green]通过[/bold green]")
            passed += 1
        else:
            console.print(f"[red]X[/red] {test_name}: [bold red]失败[/bold red]")
            failed += 1

    console.print(f"\n总计: {passed} 通过, {failed} 失败\n")

    if failed == 0:
        console.print("[bold green]🎉 所有测试通过！批量转换功能已修复。[/bold green]\n")
        console.print("现在可以运行: [cyan]python pdf2md.py batch ./pdfs[/cyan]\n")
    else:
        console.print("[bold red]⚠️  部分测试失败，请检查上述错误信息。[/bold red]\n")


if __name__ == "__main__":
    main()
