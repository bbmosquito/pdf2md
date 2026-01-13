═════════════════════════════════════════════════════════════════════
                    PDF2MD 项目使用指导手册
                    Version 1.0 | 2025-01-13
═════════════════════════════════════════════════════════════════════

【目录】
一、项目简介
二、系统要求
三、安装指南
四、快速入门
五、详细功能说明
六、配置说明
七、性能优化建议
八、常见问题及解决方法
九、故障排查流程
十、技术支持
═════════════════════════════════════════════════════════════════════


┌─────────────────────────────────────────────────────────────────┐
│ 一、项目简介                                                      │
└─────────────────────────────────────────────────────────────────┘

PDF2MD 是一个高精度的 PDF 到 Markdown 转换工具，专门针对大型扫描 PDF
文件和 AMD 平台进行了优化。

【核心特性】
⚡ GPU 加速 - 自动检测并使用 AMD/NVIDIA/Apple GPU，速度提升 4 倍
💾 内存优化 - 智能内存管理，可处理超大型 PDF (>200MB)
🔍 高级 OCR - 使用 Docling 的先进 OCR 技术 (RapidOCR)
🚀 批量处理 - 支持多文件并行转换，自动优化工作线程数
🖼️  图像提取 - 自动提取图片到独立文件夹
📐 公式处理 - LaTeX 公式保存为图像
📊 进度跟踪 - 实时显示转换进度和性能指标
🎯 平台优化 - 针对 AMD AI MAX+ 395/8060S 专门优化

【性能对比】(899页PDF文件)
┌──────────────┬───────────┬──────────┐
│ 平台         │ 处理时间  │ 相对提升 │
├──────────────┼───────────┼──────────┤
│ Intel Ultra9 │ 60 分钟   │ 1.0x     │
│ AMD CPU优化  │ 30 分钟   │ 2.0x     │
│ AMD GPU加速  │ 15 分钟   │ 4.0x     │
└──────────────┴───────────┴──────────┘


┌─────────────────────────────────────────────────────────────────┐
│ 二、系统要求                                                      │
└─────────────────────────────────────────────────────────────────┘

【最低配置】
● CPU: 双核处理器
● 内存: 8GB RAM
● 硬盘: 500MB 可用空间
● 操作系统: Windows 10/11, Linux, macOS
● Python: 3.10 或更高版本

【推荐配置】
● CPU: 8核或更多核心 (AMD Ryzen/EPYC, Intel Core/Xeon)
● 内存: 32GB RAM 或更多
● 硬盘: 10GB 可用空间 (SSD 推荐)
● GPU (可选): AMD ROCm / NVIDIA CUDA / Apple MPS
● 操作系统: Windows 11, Ubuntu 20.04+, macOS 12+

【最佳配置】(用于大型PDF批量处理)
● CPU: AMD Threadripper / EPYC (32核+)
● 内存: 128GB RAM
● GPU: AMD AI MAX+ 395 / NVIDIA RTX 4090
● 硬盘: NVMe SSD


┌─────────────────────────────────────────────────────────────────┐
│ 三、安装指南                                                      │
└─────────────────────────────────────────────────────────────────┘

【方法一：自动安装 (推荐)】

Windows 用户:
  1. 以管理员身份运行 install.bat
  2. 按照屏幕提示完成安装
  3. 等待自动下载和配置完成

自动安装脚本将完成:
  ✓ 检测并安装 Python 3.10+
  ✓ 配置 pip 国内镜像源 (清华大学)
  ✓ 安装所有项目依赖
  ✓ 安装 Docling OCR 引擎
  ✓ 安装 PyTorch (GPU 加速支持)
  ✓ 配置环境变量
  ✓ 验证安装

【方法二：手动安装】

1. 安装 Python
   下载: https://www.python.org/downloads/
   安装时勾选 "Add Python to PATH"

2. 安装依赖
   pip install -r requirements.txt

3. 安装 Docling
   pip install docling[ocr]

4. 安装 PyTorch (可选，用于GPU加速)

   NVIDIA GPU:
   pip install torch torchvision torchaudio

   AMD GPU (Linux):
   pip install torch --index-url https://download.pytorch.org/whl/rocm

   CPU only:
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

5. 验证安装
   python -c "import docling; print('安装成功')"

【方法三：使用国内镜像加速安装】

如果下载速度慢，使用以下命令:

pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

然后执行:
pip install -r requirements.txt
pip install docling[ocr]


┌─────────────────────────────────────────────────────────────────┐
│ 四、快速入门                                                      │
└─────────────────────────────────────────────────────────────────┘

【1. 转换单个 PDF 文件】

基本用法:
  python pdf2md.py convert document.pdf

这将在 document_md/ 目录下生成:
  ├── document.md          # 主 Markdown 文件
  └── images/              # 提取的图像文件夹
      ├── image_0001.png
      ├── image_0002.png
      └── ...

指定输出目录:
  python pdf2md.py convert document.pdf -o ./output

禁用 GPU (使用CPU):
  python pdf2md.py convert document.pdf --no-gpu

【2. 批量转换多个 PDF】

转换目录下所有 PDF:
  python pdf2md.py batch ./pdfs

指定工作线程数:
  python pdf2md.py batch ./pdfs --workers 8

递归搜索子目录:
  python pdf2md.py batch ./pdfs --recursive

【3. 转换指定文件】

python pdf2md.py multiple file1.pdf file2.pdf file3.pdf

【4. 查看系统信息】

python pdf2md.py info

将显示:
  - CPU 核心数
  - 内存大小
  - GPU 信息
  - Python 版本
  - 已安装的依赖版本

【5. 运行性能测试】

python benchmark.py test.pdf

这会测试不同配置下的性能，并输出优化建议。


┌─────────────────────────────────────────────────────────────────┐
│ 五、详细功能说明                                                  │
└─────────────────────────────────────────────────────────────────┘

【convert 命令 - 转换单个PDF】

用法: python pdf2md.py convert [OPTIONS] PDF

选项说明:
  -o, --output DIR          输出目录 (默认: PDF名称_md/)
  -w, --workers INT         并行工作线程数 (默认: 自动检测)
  --ocr/--no-ocr            启用/禁用 OCR (默认: 启用)
  --dpi INT                 渲染图像 DPI (默认: 200)
  --gpu/--no-gpu            启用/禁用 GPU 加速 (默认: 自动检测)
  --device {auto,cuda,mps,cpu}  加速设备 (默认: auto)
  --batch-size INT          OCR/布局批处理大小 (默认: 自动检测)

使用示例:

# 1. 基本转换 (自动检测最优设置)
python pdf2md.py convert report.pdf

# 2. 指定输出目录
python pdf2md.py convert report.pdf -o C:\output\converted

# 3. 强制使用 CPU 模式
python pdf2md.py convert report.pdf --no-gpu

# 4. 高质量输出 (300 DPI)
python pdf2md.py convert report.pdf --dpi 300

# 5. GPU 内存充足时增大批处理大小
python pdf2md.py convert report.pdf --batch-size 128

# 6. 指定工作线程数 (适合多核CPU)
python pdf2md.py convert report.pdf --workers 16

【batch 命令 - 批量转换】

用法: python pdf2md.py batch [OPTIONS] DIRECTORY

选项说明:
  -o, --output DIR          输出目录
  --pattern GLOB            文件匹配模式 (默认: *.pdf)
  -r, --recursive           递归搜索子目录
  -w, --workers INT         并行工作线程数
  --ocr/--no-ocr            启用/禁用 OCR

使用示例:

# 1. 转换当前目录所有 PDF
python pdf2md.py batch .

# 2. 转换指定目录
python pdf2md.py batch C:\documents\pdfs

# 3. 递归转换所有子目录
python pdf2md.py batch . --recursive

# 4. 只转换匹配特定模式的文件
python pdf2md.py batch . --pattern "report_*.pdf"

# 5. 使用 12 个并行工作线程
python pdf2md.py batch . --workers 12

【multiple 命令 - 多文件转换】

用法: python pdf2md.py multiple [OPTIONS] PDF1 [PDF2 ...]

示例:
  python pdf2md.py multiple file1.pdf file2.pdf file3.pdf

支持与 convert 命令相同的所有选项。

【benchmark 命令 - 性能测试】

用法: python benchmark.py PDF [OPTIONS]

选项:
  -o, --output FILE         保存结果到 JSON 文件

示例:
  # 测试并显示结果
  python benchmark.py large_report.pdf

  # 测试并保存结果
  python benchmark.py large_report.pdf -o results.json

性能测试会评估:
  ✓ CPU 模式性能
  ✓ GPU 模式性能 (如有)
  ✓ 不同批处理大小的影响
  ✓ 内存使用情况
  ✓ 处理速度


┌─────────────────────────────────────────────────────────────────┐
│ 六、配置说明                                                      │
└─────────────────────────────────────────────────────────────────┘

【配置文件位置】
config.yaml (项目根目录)

【主要配置项】

1. 转换设置 (conversion)
   output_format: markdown              # 输出格式
   ocr_enabled: true                    # 启用 OCR
   ocr_languages: ["en", "zh-CN"]       # OCR 语言

2. 内存管理 (memory)
   max_pages_in_memory: 20             # 内存中最大页数
   process_chunk_size: 15              # 处理块大小

   推荐配置:
   - 大内存系统 (>=64GB): 20 / 15
   - 中等内存 (16-32GB): 10 / 10
   - 小内存 (<16GB): 5 / 5

3. 处理设置 (processing)
   max_workers: 12                      # 最大工作线程
   dpi: 200                            # 渲染 DPI

   推荐配置:
   - 8核CPU: workers = 8
   - 16核CPU: workers = 12-16
   - 32核CPU: workers = 24-32

4. 性能优化 (performance)
   enable_gpu: true                    # 启用 GPU
   accelerator_device: "auto"          # 加速设备
   num_threads: null                   # 线程数 (null=自动)

   ocr_batch_size: 64                  # OCR 批处理大小
   layout_batch_size: 64               # 布局分析批处理
   table_batch_size: 8                 # 表格处理批处理

   批处理大小推荐:
   GPU内存 <4GB:   8-16
   GPU内存 4-8GB:  16-32
   GPU内存 8-16GB: 32-64
   GPU内存 >16GB:  64-128

5. 输出设置 (output)
   save_images: true                   # 保存图像
   image_format: png                   # 图像格式
   extract_formulas_as_images: true   # 公式提取为图像

【配置示例】

# 针对大内存系统 (96GB+ RAM)
memory:
  max_pages_in_memory: 30
  process_chunk_size: 20

processing:
  max_workers: 24

performance:
  ocr_batch_size: 128
  layout_batch_size: 128

# 针对小内存系统 (8-16GB RAM)
memory:
  max_pages_in_memory: 5
  process_chunk_size: 5

processing:
  max_workers: 4

performance:
  ocr_batch_size: 16
  layout_batch_size: 16


┌─────────────────────────────────────────────────────────────────┐
│ 七、性能优化建议                                                  │
└─────────────────────────────────────────────────────────────────┘

【1. GPU 加速优化】

启用 GPU 可获得 2-4x 性能提升:

# 自动检测并启用 GPU
python pdf2md.py convert doc.pdf

# 显式指定 GPU
python pdf2md.py convert doc.pdf --device cuda

不同 GPU 的推荐批处理大小:
┌──────────────┬──────────┬──────────────┐
│ GPU 内存     │ batch    │ 适用场景     │
├──────────────┼──────────┼──────────────┤
│ <4GB         │ 8-16     │ 入门级 GPU   │
│ 4-8GB        │ 16-32    │ 主流 GPU     │
│ 8-16GB       │ 32-64    │ 中高端 GPU   │
│ >16GB        │ 64-128   │ 专业级 GPU   │
└──────────────┴──────────┴──────────────┘

【2. CPU 多核优化】

根据 CPU 核心数调整工作线程:
  # 查看核心数
  python pdf2md.py info

  # 设置工作线程数 (建议为物理核心数的 75%)
  python pdf2md.py convert doc.pdf --workers 24

【3. 内存优化】

处理超大 PDF 时的内存优化:
  # 减少批处理大小
  python pdf2md.py convert large.pdf --batch-size 16

  # 减少工作线程
  python pdf2md.py convert large.pdf --workers 4

【4. 批量处理优化】

批量转换多个文件时的优化建议:
  # 使用合理的并行度
  python pdf2md.py batch ./pdfs --workers 8

  # 避免同时转换过多超大文件
  # 建议分批处理: 先处理小文件，再处理大文件

【5. 系统资源监控】

在转换过程中监控系统资源:
  # Windows: 任务管理器 → 性能
  # Linux: htop 或 nvidia-smi

关注指标:
  - CPU 使用率 (目标: 80-95%)
  - GPU 使用率 (目标: 70-90%)
  - 内存使用 (目标: <80%)
  - GPU 内存 (目标: <85%)


┌─────────────────────────────────────────────────────────────────┐
│ 八、常见问题及解决方法                                            │
└─────────────────────────────────────────────────────────────────┘

【问题1: Docling 未安装】

症状:
  ModuleNotFoundError: No module named 'docling'

解决方案:
  pip install docling[ocr]

或使用国内镜像:
  pip install docling[ocr] -i https://pypi.tuna.tsinghua.edu.cn/simple

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【问题2: GPU 未检测到】

症状:
  日志显示 "No GPU detected, using CPU"

解决方案:

1. 验证 PyTorch 安装:
   python -c "import torch; print(torch.cuda.is_available())"

   如果输出 False，继续下一步。

2. 重新安装 PyTorch (NVIDIA GPU):
   pip uninstall torch -y
   pip install torch torchvision torchaudio

3. 重新安装 PyTorch (AMD GPU on Linux):
   pip uninstall torch -y
   pip install torch --index-url https://download.pytorch.org/whl/rocm

4. 更新 Docling:
   pip install --upgrade docling

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【问题3: 内存不足 (MemoryError)】

症状:
  MemoryError: Unable to allocate array
  或系统卡死、程序崩溃

解决方案:

1. 减少批处理大小:
   python pdf2md.py convert doc.pdf --batch-size 8

2. 减少工作线程:
   python pdf2md.py convert doc.pdf --workers 2

3. 禁用 GPU:
   python pdf2md.py convert doc.pdf --no-gpu

4. 修改 config.yaml:
   memory:
     max_pages_in_memory: 3
     process_chunk_size: 3

   performance:
     ocr_batch_size: 4
     layout_batch_size: 4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【问题4: OCR 识别质量差】

症状:
  识别出的文字错误多
  中文识别不准确
  表格识别错误

解决方案:

1. 提高 DPI:
   python pdf2md.py convert doc.pdf --dpi 300

2. 检查 OCR 语言配置 (config.yaml):
   ocr_languages:
     - en           # 英文
     - zh-CN        # 简体中文
     - zh-TW        # 繁体中文

3. 确保原图清晰度足够:
   - 扫描PDF: 建议 300 DPI 以上
   - 电子PDF: 通常质量较好

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【问题5: 转换速度慢】

症状:
  处理时间过长
  CPU/GPU 使用率低

解决方案:

1. 运行性能测试:
   python benchmark.py your_file.pdf

2. 根据建议调整配置:
   - 启用 GPU (如有)
   - 增加批处理大小
   - 增加工作线程

3. 检查系统资源:
   - 关闭其他占用资源的程序
   - 确保没有其他进程占用 GPU

4. 升级硬件:
   - 增加内存
   - 使用更好的 GPU

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【问题6: 程序无响应或卡死】

症状:
  程序运行一段时间后无响应
  进度条不动

解决方案:

1. 检查是否内存耗尽:
   # Windows 任务管理器
   # Linux: free -h

2. 减少并发数:
   python pdf2md.py convert doc.pdf --workers 1 --batch-size 4

3. 分段处理大文件:
   # 先处理前100页
   # 再处理剩余部分

4. 查看日志:
   # 检查 pdf2md.log 中的错误信息

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【问题7: 依赖包冲突】

症状:
  ImportError: cannot import name 'xxx'
  或版本不兼容错误

解决方案:

1. 查看已安装包版本:
   pip list

2. 更新冲突的包:
   pip install --upgrade package_name

3. 重新安装所有依赖:
   pip uninstall -y docling pymupdf Pillow rich click pyyaml psutil torch
   pip install -r requirements.txt
   pip install docling[ocr]

4. 使用虚拟环境 (推荐):
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   pip install docling[ocr]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【问题8: Windows 上权限错误】

症状:
  PermissionError: [WinError 5] Access is denied

解决方案:

1. 以管理员身份运行:
   右键 install.bat → 以管理员身份运行

2. 检查文件夹权限:
   - 确保对输出目录有写权限
   - 临时关闭杀毒软件

3. 更换输出目录:
   python pdf2md.py convert doc.pdf -o C:\output

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【问题9: 网络下载失败】

症状:
  下载 Python 或依赖包时超时/失败

解决方案:

1. 使用国内镜像:
   pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

2. 尝试其他镜像源:
   # 阿里云
   pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

   # 中科大
   pip config set global.index-url https://pypi.mirrors.ustc.edu.cn/simple/

3. 手动下载安装:
   # 从国内网站下载 Python 安装包
   # https://npmmirror.com/mirrors/python/

4. 使用代理 (如可用):
   pip install --proxy http://127.0.0.1:7890 package_name

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【问题10: 输出格式问题】

症状:
  Markdown 格式混乱
  表格错位
  图片未正确引用

解决方案:

1. 这通常是 PDF 源文件的问题
2. 尝试提高 DPI 获得更好的识别效果
3. 人工后期校对和格式调整
4. 检查是否为扫描版 PDF (OCR 误差较大)


┌─────────────────────────────────────────────────────────────────┐
│ 九、故障排查流程                                                  │
└─────────────────────────────────────────────────────────────────┘

【系统故障排查步骤】

步骤1: 检查环境
  ✓ 打开命令行，输入: python --version
  ✓ 应显示 Python 3.10.x 或更高版本

步骤2: 验证安装
  ✓ 输入: python -c "import docling; print(docling.__version__)"
  ✓ 应显示 Docling 版本号

步骤3: 检查 GPU
  ✓ 输入: python -c "import torch; print(torch.cuda.is_available())"
  ✓ 如果有 GPU，应显示 True

步骤4: 查看系统信息
  ✓ 输入: python pdf2md.py info
  ✓ 查看各项配置是否正确

步骤5: 测试简单文件
  ✓ 先用小型 PDF 测试
  ✓ 确认基本功能正常后再处理大文件

步骤6: 查看日志
  ✓ 检查 pdf2md.log
  ✓ 查找错误信息和警告

步骤7: 运行基准测试
  ✓ 输入: python benchmark.py test.pdf
  ✓ 获取性能报告和优化建议

【性能问题排查】

如果转换速度慢:

1. 运行 benchmark.py 获取性能基线
2. 检查 CPU/GPU 使用率
3. 尝试不同配置:
   - 启用/禁用 GPU
   - 调整 batch_size
   - 调整 workers
4. 根据系统资源优化配置
5. 考虑硬件升级

【内存问题排查】

如果出现内存不足:

1. 关闭其他程序
2. 减少批处理大小
3. 减少工作线程
4. 处理更小的文件
5. 增加系统内存 (长期方案)


┌─────────────────────────────────────────────────────────────────┐
│ 十、技术支持                                                      │
└─────────────────────────────────────────────────────────────────┘

【文档资源】

项目包含以下文档:
  - README.md: 项目总体介绍
  - QUICKSTART_AMD.md: 快速入门指南
  - PERFORMANCE_OPTIMIZATION.md: 性能优化详解
  - Readme.txt: 本文件

【日志文件】

pdf2md.log - 详细运行日志
  包含每次转换的:
  - 系统配置信息
  - 处理进度
  - 性能指标
  - 错误和警告

【获取帮助】

1. 查看文档:
   优先查看项目自带的文档文件

2. 运行诊断:
   python pdf2md.py info
   python benchmark.py test.pdf

3. 检查日志:
   查看 pdf2md.log 获取详细信息

4. 重新安装:
   如果问题持续，尝试重新安装:
   pip uninstall -y docling pymupdf Pillow
   pip install -r requirements.txt
   pip install docling[ocr]

【最佳实践】

1. 首次使用:
   - 先用小文件测试
   - 熟悉命令行选项
   - 查看 config.yaml 配置

2. 处理大文件:
   - 确保足够内存
   - 考虑使用 GPU 加速
   - 监控系统资源

3. 批量处理:
   - 合理设置并行度
   - 分批处理超大文件
   - 定期检查输出

4. 性能优化:
   - 运行 benchmark 测试
   - 根据硬件调整配置
   - 更新到最新版本


【附录: 快速参考】

常用命令:
  python pdf2md.py convert file.pdf              # 基本转换
  python pdf2md.py convert file.pdf -o output   # 指定输出
  python pdf2md.py convert file.pdf --no-gpu     # CPU模式
  python pdf2md.py batch ./pdfs                  # 批量转换
  python pdf2md.py info                          # 系统信息
  python benchmark.py test.pdf                  # 性能测试

配置文件: config.yaml
日志文件: pdf2md.log
测试文件: test_complete_system.py


═════════════════════════════════════════════════════════════════════
                        文档结束
                   版本: 1.0 | 2025-01-13
═════════════════════════════════════════════════════════════════════
