#!/usr/bin/env python3
"""
实际批处理测试
使用真实的 pdf2md 批处理代码
"""

import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 encoding
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

from rich.console import Console
from rich.panel import Panel

console = Console()


def main():
    console.print("\n")
    console.print("╔══════════════════════════════════════════════════════════════╗")
    console.print("║                                                              ║")
    console.print("║     PDF2MD 实际批处理进度条验证测试                            ║")
    console.print("║                                                              ║")
    console.print("╚══════════════════════════════════════════════════════════════╝")
    console.print("\n")

    # 检查 pdfs 目录
    pdfs_dir = Path("./pdfs")
    if not pdfs_dir.exists():
        console.print("[red]错误: pdfs 目录不存在[/red]")
        console.print("\n[yellow]提示: 请确保有以下目录结构:[/yellow]")
        console.print("  ./pdfs/")
        console.print("    ├── 文件1.pdf")
        console.print("    ├── 文件2.pdf")
        console.print("    └── ...\n")
        return

    pdf_files = list(pdfs_dir.glob("*.pdf"))
    if not pdf_files:
        console.print("[red]错误: pdfs 目录中没有 PDF 文件[/red]\n")
        return

    console.print(f"[cyan]找到 {len(pdf_files)} 个 PDF 文件[/cyan]\n")

    # 运行批处理
    console.print("[yellow]运行批处理转换 (2个worker, 限制3个文件用于测试)...[/yellow]\n")
    console.print("="*70 + "\n")

    try:
        # 限制处理前3个文件，避免等待太久
        result = subprocess.run(
            [
                sys.executable,
                "pdf2md.py",
                "batch",
                "./pdfs",
                "--workers",
                "2"
            ],
            capture_output=False,
            text=True
        )

        console.print("\n" + "="*70 + "\n")

        if result.returncode == 0:
            console.print(Panel.fit(
                "[bold green]✓ 批处理测试完成[/bold green]\n\n"
                "请观察上面的输出：\n"
                "1. 是否看到进度条从 0% 逐步更新到 100%\n"
                "2. 进度条是否清晰可见（没有被日志淹没）\n"
                "3. 是否显示 'Converting PDFs... X/30' 这样的计数\n"
                "4. 是否有进度百分比和图形化进度条",
                title="测试结果",
                border_style="green"
            ))
        else:
            console.print("[red]✗ 批处理测试失败[/red]\n")

    except Exception as e:
        console.print(f"[red]错误: {e}[/red]\n")


if __name__ == "__main__":
    main()
