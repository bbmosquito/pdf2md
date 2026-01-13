@echo off
chcp 65001 >nul
echo ========================================
echo   PDF2MD 项目 GitHub 发布助手
echo   Version 1.0
echo ========================================
echo.
echo 此脚本将帮助您将项目发布到GitHub
echo 请确保您已经:
echo   1. 创建了GitHub账号
echo   2. 生成了Personal Access Token
echo   3. 安装了Git
echo.
echo 按任意键继续，或关闭窗口退出...
pause >nul
cls

:: ========================================
:: 步骤1: 检查Git安装
:: ========================================
echo.
echo ========================================
echo [1/7] 检查 Git 安装...
echo ========================================
echo.

git --version >nul 2>&1
if %errorLevel% == 0 (
    for /f "tokens=3" %%i in ('git --version') do (
        echo [√] 检测到 Git: %%i
    )
) else (
    echo [×] 未检测到 Git
    echo.
    echo 请先安装 Git:
    echo 下载地址: https://git-scm.com/downloads
    echo.
    pause
    exit /b 1
)

echo.
pause
cls

:: ========================================
:: 步骤2: 获取GitHub用户信息
:: ========================================
echo.
echo ========================================
echo [2/7] 配置 GitHub 信息...
echo ========================================
echo.

echo 请提供您的GitHub信息（此信息仅用于本次发布）
echo.

set /p GITHUB_USERNAME="GitHub用户名: "
echo.

if "%GITHUB_USERNAME%"=="" (
    echo [!] 用户名不能为空
    pause
    exit /b 1
)

echo [√] 用户名: %GITHUB_USERNAME%
echo.
pause
cls

:: ========================================
:: 步骤3: 创建.gitignore文件
:: ========================================
echo.
echo ========================================
echo [3/7] 创建 .gitignore 文件...
echo ========================================
echo.

echo 正在创建 .gitignore 文件...
echo.

(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo build/
echo develop-eggs/
echo dist/
echo downloads/
echo eggs/
echo .eggs/
echo lib/
echo lib64/
echo parts/
echo sdist/
echo var/
echo wheels/
echo *.egg-info/
echo .installed.cfg
echo *.egg
echo MANIFEST
echo.
echo # Virtual Environment
echo venv/
echo env/
echo ENV/
echo.
echo # Project specific
echo *.log
echo pdf2md.log
echo .DS_Store
echo tmpclaude-*
echo *.tmp
echo nul
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.swp
echo *.swo
echo *~
echo.
echo # OS
echo Thumbs.db
echo .DS_Store
) > .gitignore

echo [√] .gitignore 文件创建完成
echo.
pause
cls

:: ========================================
:: 步骤4: 初始化Git仓库
:: ========================================
echo.
echo ========================================
echo [4/7] 初始化 Git 仓库...
echo ========================================
echo.

echo 正在初始化Git仓库...
git init

echo.
echo 正在配置Git用户信息...
git config user.name "PDF2MD Publisher"
git config user.email "pdf2md@example.com"

echo [√] Git 仓库初始化完成
echo.
pause
cls

:: ========================================
:: 步骤5: 添加文件到Git
:: ========================================
echo.
echo ========================================
echo [5/7] 添加项目文件...
echo ========================================
echo.

echo 正在添加所有文件到Git...
git add .

echo.
echo 正在创建首次提交...
git commit -m "Initial commit: PDF2MD v1.0

- PDF to Markdown converter with GPU acceleration
- Support for AMD ROCm, NVIDIA CUDA, Apple MPS
- Automatic installation script (install.bat)
- Complete documentation and user guide
- Performance benchmarking tools

Features:
- High-precision OCR (Docling/RapidOCR)
- Memory-efficient processing for large PDFs
- Batch processing support
- Real-time progress tracking
- Automatic hardware detection

Performance:
- 4x faster with GPU acceleration
- Optimized for AMD AI MAX+ 395/8060S
- Intelligent memory management"

if %errorLevel% == 0 (
    echo.
    echo [√] 文件提交完成
) else (
    echo.
    echo [!] 提交失败
    pause
    exit /b 1
)

echo.
pause
cls

:: ========================================
:: 步骤6: 创建GitHub仓库
:: ========================================
echo.
echo ========================================
echo [6/7] 在 GitHub 上创建仓库...
echo ========================================
echo.

echo 现在需要在GitHub上手动创建仓库:
echo.
echo 步骤:
echo   1. 打开浏览器，访问: https://github.com/new
echo   2. 填写仓库信息:
echo      - Repository name: pdf2md
echo      - Description: High-precision PDF to Markdown converter
echo      - 选择 Public 或 Private
echo   3. ⚠️ 不要勾选 "Add a README file"
echo   4. ⚠️ 不要勾选 "Add .gitignore"
echo   5. ⚠️ 不要勾选 "Choose a license"
echo   6. 点击 "Create repository"
echo.
echo 完成后按任意键继续...
pause >nul

echo.
echo [√] 假设您已在GitHub上创建了仓库
echo.
pause
cls

:: ========================================
:: 步骤7: 推送到GitHub
:: ========================================
echo.
echo ========================================
echo [7/7] 推送到 GitHub...
echo ========================================
echo.

echo 正在关联远程仓库...
git remote add origin https://github.com/%GITHUB_USERNAME%/pdf2md.git

echo.
echo 正在推送到GitHub...
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 重要提示:
echo.
echo 当提示输入凭据时:
echo   1. Username: 输入您的GitHub用户名
echo   2. Password: 输入您的 Personal Access Token (不是密码！)
echo.
echo 如果您还没有创建Token:
echo   1. 访问: https://github.com/settings/tokens
echo   2. 点击 "Generate new token (classic)"
echo   3. 勾选 "repo" 权限
echo   4. 生成并复制Token
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

pause

git branch -M main
git push -u origin main

if %errorLevel% == 0 (
    echo.
    echo ========================================
    echo   🎉 发布成功！
    echo ========================================
    echo.
    echo 您的项目已成功发布到GitHub!
    echo.
    echo 仓库地址:
    echo   https://github.com/%GITHUB_USERNAME%/pdf2md
    echo.
    echo 下一步:
    echo   1. 访问上述地址查看您的仓库
    echo   2. 点击 "Releases" 创建第一个Release
    echo   3. 上传 PDF2MD_Complete_Package_v1.0.zip
    echo   4. 添加开源许可证 (推荐 MIT License)
    echo   5. 分享给其他用户
    echo.
    echo 感谢使用 PDF2MD！
) else (
    echo.
    echo ========================================
    echo   [!] 推送失败
    echo ========================================
    echo.
    echo 可能的原因:
    echo   1. GitHub上的仓库尚未创建
    echo   2. 用户名或Token错误
    echo   3. 网络连接问题
    echo.
    echo 解决方法:
    echo   1. 检查是否在GitHub上创建了名为 pdf2md 的仓库
    echo   2. 确认Token有 repo 权限
    echo   3. 尝试再次运行此脚本
    echo.
    echo 如需帮助，请查看: GITHUB_PUBLISH_GUIDE.txt
)

echo.
echo ========================================
pause
