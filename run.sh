#!/bin/bash
# Dayflow macOS/Linux 启动器

echo "===================================="
echo "  Dayflow - 正在启动..."
echo "===================================="
echo

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误：未安装 Python 3"
    echo "请从 https://www.python.org/ 安装 Python 3.8+"
    exit 1
fi

# 检查依赖是否安装
python3 -c "import mss" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "正在安装依赖..."
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误：依赖安装失败"
        exit 1
    fi
fi

# 运行 Dayflow
echo "正在启动 Dayflow..."
python3 run.py
