@echo off
REM Dayflow Windows 启动器
REM 双击此文件在 Windows 上运行 Dayflow

echo ====================================
echo   Dayflow - 正在启动...
echo ====================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：Python 未安装或不在 PATH 中
    echo.
    echo 请从 https://www.python.org/ 安装 Python 3.8+
    echo 安装时请确保勾选"Add Python to PATH"
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import mss" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误：依赖安装失败
        pause
        exit /b 1
    )
)

REM 运行 Dayflow
echo 正在启动 Dayflow...
python run.py

pause
