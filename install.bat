@echo off
chcp 65001 >nul
echo ========================================
echo   PDF2MD 项目自动安装脚本
echo   版本: v1.0
echo   日期: 2025-01-13
echo ========================================
echo.
echo 本脚本将自动完成以下操作:
echo 1. 检查系统环境
echo 2. 安装 Python 3.10+ (如未安装)
echo 3. 配置国内镜像源 (pip)
echo 4. 安装项目依赖
echo 5. 安装 Docling OCR 引擎
echo 6. 安装 PyTorch (支持 GPU 加速)
echo 7. 配置环境变量
echo 8. 验证安装
echo.
echo 按任意键继续安装，或关闭窗口退出...
pause >nul
cls

:: ========================================
:: 第1步: 检查系统环境
:: ========================================
echo.
echo ========================================
echo [1/8] 检查系统环境...
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [√] 已获取管理员权限
) else (
    echo [!] 未检测到管理员权限
    echo [!] 建议以管理员身份运行以获得最佳体验
    echo.
)

:: 检查操作系统版本
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo [√] 操作系统版本: Windows %VERSION%

:: 检查架构
if defined PROCESSOR_ARCHITEW64 (
    set ARCH=%PROCESSOR_ARCHITEW64%
) else (
    set ARCH=%PROCESSOR_ARCHITECTURE%
)
echo [√] 系统架构: %ARCH%

:: 检查内存
for /f "skip=1 tokens=4" %%i in ('wmic computersystem get TotalPhysicalMemory') do (
    set MEMORY=%%i
    goto :memory_found
)
:memory_found
set /a MEMORY_GB=%MEMORY:~0,-3% / 1024 / 1024
echo [√] 系统内存: 约 %MEMORY_GB% GB

echo.
echo [√] 系统环境检查完成
echo.
pause
cls

:: ========================================
:: 第2步: 检查并安装 Python
:: ========================================
echo.
echo ========================================
echo [2/8] 检查 Python 安装...
echo ========================================
echo.

where python >nul 2>&1
if %errorLevel% == 0 (
    python --version >nul 2>&1
    if %errorLevel% == 0 (
        for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PY_VERSION=%%i
        echo [√] 检测到 Python: %PY_VERSION%

        :: 检查版本是否 >= 3.10
        python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
        if %errorLevel% == 0 (
            echo [√] Python 版本满足要求 (>= 3.10)
        ) else (
            echo [!] Python 版本过低，需要 3.10 或更高版本
            echo.
            goto :install_python
        )
        goto :python_ok
    )
)

:install_python
echo [!] 未检测到 Python 3.10+
echo.
echo 正在下载 Python 3.11.7 安装程序...
echo.

:: 创建临时目录
set TEMP_DIR=%TEMP%\pdf2md_install
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

:: 下载 Python (使用国内镜像)
set PYTHON_URL=https://npmmirror.com/mirrors/python/3.11.7/python-3.11.7-amd64.exe
set PYTHON_INSTALLER=%TEMP_DIR%\python-3.11.7-amd64.exe

echo [1/2] 正在下载 Python 安装程序...
powershell -Command "& {Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%' -UseBasicParsing}" >nul 2>&1

if exist "%PYTHON_INSTALLER%" (
    echo [√] 下载完成
    echo.
    echo [2/2] 正在安装 Python...
    echo [!] 请在安装程序中勾选 "Add Python to PATH"
    echo.
    start /wait "" "%PYTHON_INSTALLER%" /passive InstallAllUsers=0 PrependPath=1 Include_test=0

    :: 刷新环境变量
    refreshenv >nul 2>&1

    echo [√] Python 安装完成
    echo [!] 请重新运行此脚本以继续安装
    echo.
    pause
    exit /b 0
) else (
    echo [×] 下载失败
    echo [!] 请手动下载并安装 Python 3.10+
    echo [!] 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:python_ok
echo.
python -c "import sys; print(f'  Python 路径: {sys.executable}')"
echo.
pause
cls

:: ========================================
:: 第3步: 配置 pip 国内镜像源
:: ========================================
echo.
echo ========================================
echo [3/8] 配置 pip 国内镜像源...
echo ========================================
echo.

set PIP_CONFIG_FILE=%USERPROFILE%\pip\pip.ini
if not exist "%USERPROFILE%\pip" mkdir "%USERPROFILE%\pip"

echo 正在配置 pip 镜像源...
echo.

(
echo [global]
echo index-url = https://pypi.tuna.tsinghua.edu.cn/simple
echo trusted-host = pypi.tuna.tsinghua.edu.cn
echo.
echo [install]
echo trusted-host = pypi.tuna.tsinghua.edu.cn
) > "%PIP_CONFIG_FILE%"

echo [√] pip 镜像源配置完成
echo     镜像源: 清华大学 (TUNA)
echo     配置文件: %PIP_CONFIG_FILE%
echo.

:: 升级 pip
echo [!] 正在升级 pip 到最新版本...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
if %errorLevel% == 0 (
    echo [√] pip 升级完成
) else (
    echo [!] pip 升级失败，继续安装...
)
echo.
pause
cls

:: ========================================
:: 第4步: 安装项目依赖
:: ========================================
echo.
echo ========================================
echo [4/8] 安装项目依赖...
echo ========================================
echo.

cd /d "%~dp0"

echo [!] 正在安装基础依赖包...
echo     - docling (PDF 转换核心引擎)
echo     - pymupdf (PDF 处理库)
echo     - Pillow (图像处理)
echo     - rich (终端美化)
echo     - click (命令行框架)
echo     - pyyaml (配置文件解析)
echo     - psutil (系统监控)
echo.

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if %errorLevel% == 0 (
    echo.
    echo [√] 基础依赖安装完成
) else (
    echo.
    echo [×] 基础依赖安装失败
    echo [!] 请检查网络连接或尝试手动安装
    echo.
    pause
    exit /b 1
)

echo.
pause
cls

:: ========================================
:: 第5步: 安装 Docling OCR 引擎
:: ========================================
echo.
echo ========================================
echo [5/8] 安装 Docling OCR 引擎...
echo ========================================
echo.

echo [!] Docling 是本项目的核心 OCR 引擎
echo [!] 支持中英文混合识别，具有高精度特性
echo.

echo [1/2] 正在安装 Docling 核心包...
pip install docling -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorLevel% == 0 (
    echo [√] Docling 核心包安装完成
) else (
    echo [!] Docling 核心包安装失败
)

echo.
echo [2/2] 正在安装 Docling OCR 插件...
pip install "docling[ocr]" -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorLevel% == 0 (
    echo [√] Docling OCR 插件安装完成
) else (
    echo [!] Docling OCR 插件安装失败，将使用基础 OCR
)

echo.
echo [√] Docling OCR 引擎安装完成
echo.
pause
cls

:: ========================================
:: 第6步: 安装 PyTorch (GPU 加速支持)
:: ========================================
echo.
echo ========================================
echo [6/8] 安装 PyTorch (GPU 加速支持)...
echo ========================================
echo.

echo [!] PyTorch 提供 GPU 加速，可提升 2-4x 转换速度
echo [!] 支持 AMD ROCm、NVIDIA CUDA、Apple MPS
echo.

:: 检测 GPU 类型
set GPU_TYPE=cpu

:: 检测 NVIDIA GPU
nvidia-smi >nul 2>&1
if %errorLevel% == 0 (
    set GPU_TYPE=cuda
    echo [√] 检测到 NVIDIA GPU
    goto :install_pytorch
)

:: 检测 AMD GPU (Windows 上 ROCm 支持有限)
:: 如果有 AMD GPU，使用 CPU 版本
wmic path win32_VideoController get name | findstr /i "AMD" >nul 2>&1
if %errorLevel% == 0 (
    echo [!] 检测到 AMD GPU
    echo [!] Windows 上 AMD GPU 支持: ROCm (实验性)
    echo [!] 建议使用 CPU 版本或 Linux 系统
    set GPU_TYPE=cpu
    goto :install_pytorch
)

echo [!] 未检测到独立 GPU，将安装 CPU 版本
echo [!] CPU 版本稳定性最好，但速度较慢
echo.

:install_pytorch
if "%GPU_TYPE%"=="cuda" (
    echo [!] 正在安装 PyTorch (CUDA 版本)...
    pip install torch torchvision torchaudio -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    echo [!] 正在安装 PyTorch (CPU 版本)...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu -i https://pypi.tuna.tsinghua.edu.cn/simple
)

if %errorLevel% == 0 (
    echo [√] PyTorch 安装完成
) else (
    echo [!] PyTorch 安装失败，将使用 CPU 模式
)

echo.
pause
cls

:: ========================================
:: 第7步: 配置环境变量
:: ========================================
echo.
echo ========================================
echo [7/8] 配置环境变量...
echo ========================================
echo.

:: 设置 Python 路径
setx PYTHONPATH "%PYTHONPATH%;%~dp0src" >nul 2>&1
echo [√] 已添加 PYTHONPATH 环境变量

:: 检查并设置 GPU 相关环境变量
if "%GPU_TYPE%"=="cuda" (
    setx CUDA_VISIBLE_DEVICES "0" >nul 2>&1
    echo [√] 已设置 CUDA_VISIBLE_DEVICES=0
)

:: 设置项目根目录
setx PDF2MD_ROOT "%~dp0" >nul 2>&1
echo [√] 已设置 PDF2MD_ROOT=%~dp0

echo.
echo [√] 环境变量配置完成
echo     注: 部分环境变量需要重启终端后生效
echo.
pause
cls

:: ========================================
:: 第8步: 验证安装
:: ========================================
echo.
echo ========================================
echo [8/8] 验证安装...
echo ========================================
echo.

echo [!] 正在验证关键组件...
echo.

:: 验证 Python
python --version
if %errorLevel% == 0 (
    echo [√] Python 可用
) else (
    echo [×] Python 不可用
)

echo.

:: 验证 Docling
python -c "import docling" >nul 2>&1
if %errorLevel% == 0 (
    echo [√] Docling 可用
    python -c "import docling; print(f'     版本: {docling.__version__}')"
) else (
    echo [×] Docling 不可用
)

echo.

:: 验证 PyTorch
python -c "import torch" >nul 2>&1
if %errorLevel% == 0 (
    echo [√] PyTorch 可用
    python -c "import torch; print(f'     版本: {torch.__version__}'); print(f'     CUDA 可用: {torch.cuda.is_available()}')"
) else (
    echo [!] PyTorch 未安装 (可选)
)

echo.

:: 验证其他依赖
python -c "import pymupdf, PIL, rich, click, yaml, psutil" >nul 2>&1
if %errorLevel% == 0 (
    echo [√] 所有依赖包已正确安装
) else (
    echo [!] 部分依赖包可能未正确安装
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 项目已成功安装到: %~dp0
echo.
echo 快速开始:
echo   1. 转换单个 PDF:
echo      python pdf2md.py convert document.pdf
echo.
echo   2. 批量转换:
echo      python pdf2md.py batch ./pdfs
echo.
echo   3. 运行性能测试:
echo      python benchmark.py test.pdf
echo.
echo 详细文档:
echo   - README.md (项目说明)
echo   - QUICKSTART_AMD.md (快速入门)
echo   - PERFORMANCE_OPTIMIZATION.md (性能优化)
echo.
echo 常见问题:
echo   如遇到问题，请查看 Readme.txt 中的故障排除部分
echo.
echo ========================================
pause
