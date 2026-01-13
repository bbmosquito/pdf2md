@echo off
chcp 65001 >nul
echo ========================================
echo   修复 Hugging Face 连接问题
echo ========================================
echo.
echo 此脚本将尝试多个解决方案：
echo   1. 使用官方 Hugging Face 源
echo   2. 手动下载模型文件
echo   3. 配置代理设置（如需要）
echo.
pause
cls

:: ========================================
:: 方案1: 设置环境变量使用官方源
:: ========================================
echo.
echo ========================================
echo [方案1] 使用 Hugging Face 官方源
echo ========================================
echo.

echo 正在设置环境变量...
set HF_ENDPOINT=https://huggingface.co

echo [√] 已设置 HF_ENDPOINT=https://huggingface.co
echo.
echo 现在请尝试重新运行转换命令:
echo   python pdf2md.py convert future_option_9.pdf
echo.
echo 如果仍然失败，请按任意键继续尝试方案2...
pause
cls

:: ========================================
:: 方案2: 手动下载模型
:: ========================================
echo.
echo ========================================
echo [方案2] 手动下载布局模型
echo ========================================
echo.

echo 模型缓存目录位置:
echo %USERPROFILE%\.cache\huggingface\hub
echo.

echo 正在创建缓存目录...
if not exist "%USERPROFILE%\.cache\huggingface\hub" mkdir "%USERPROFILE%\.cache\huggingface\hub"

echo.
echo ========================================
echo 请选择下载方式:
echo ========================================
echo.
echo [1] 使用国内镜像站 (modelscope / gitee)
echo [2] 使用浏览器下载 (手动)
echo [3] 跳过，稍后手动处理
echo.
set /p choice="请输入选择 (1/2/3): "

if "%choice%"=="1" goto :method1
if "%choice%"=="2" goto :method2
if "%choice%"=="3" goto :end

:method1
echo.
echo 正在尝试使用 modelscope 镜像...
echo.
pip install modelscope >nul 2>&1

python -c "from modelscope import snapshot_download; snapshot_download('docling-project/docling-layout-heron', cache_dir='%USERPROFILE%\.cache\huggingface')" 2>nul

if %errorLevel% == 0 (
    echo [√] 模型下载完成
) else (
    echo [!] 下载失败，请尝试方案2
)
goto :end

:method2
echo.
echo ========================================
echo 手动下载说明:
echo ========================================
echo.
echo 1. 访问以下任意链接下载模型:
echo.
echo    官方源:
echo    https://huggingface.co/docling-project/docling-layout-heron
echo.
echo    镜像源 (如果官方无法访问):
echo    https://hf-mirror.com/docling-project/docling-layout-heron
echo.
echo 2. 下载后解压到:
echo    %USERPROFILE%\.cache\huggingface\hub\models--docling-project--docling-layout-heron
echo.
echo 3. 或者使用以下命令手动下载:
echo.
echo    pip install huggingface-hub
echo    huggingface-cli download docling-project/docling-layout-heron --local-dir ./models/docling-layout-heron
echo.

:end
echo.
echo ========================================
echo 修复完成
echo ========================================
echo.
echo 推荐命令:
echo   set HF_ENDPOINT=https://huggingface.co
echo   python pdf2md.py convert future_option_9.pdf
echo.
pause
