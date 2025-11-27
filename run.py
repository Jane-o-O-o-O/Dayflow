#!/usr/bin/env python3
"""
Dayflow - 自动跟踪您的一天

跨平台屏幕录制和 AI 驱动的时间线应用
支持 Windows、macOS 和 Linux
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app_controller import AppController


def main():
    """主入口点"""
    print("=" * 60)
    print("  Dayflow - 自动跟踪您的一天")
    print("=" * 60)
    print()

    # Create and run app
    app = AppController()

    # Check if first launch
    if app.config.get('first_launch', True):
        print("👋 欢迎使用 Dayflow！")
        print()
        print("开始使用：")
        print("1. 点击 ⚙️  设置 来配置您的 AI 提供商")
        print("2. 点击 🎥 开始录制 来开始跟踪")
        print("3. 您的时间线将自动出现！")
        print()
        app.config.set('first_launch', False)

    print("🚀 正在启动 Dayflow...")
    print()

    try:
        app.run()
    except KeyboardInterrupt:
        print("\n👋 正在关闭 Dayflow...")
        app.stop_services()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
