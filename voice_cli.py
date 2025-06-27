#!/usr/bin/env python
# Copyright (c) 2025, Williams.Wang. All rights reserved. Use restricted under LICENSE terms.

"""
Voice Recording and Transcription Tool - 启动脚本

这是一个便于使用的启动脚本，可以直接运行整个语音转写工具。
直接运行 `python voice_cli.py` 默认执行录音功能。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主入口函数，处理默认命令和导入"""
    try:
        # 导入CLI模块
        from src.cli.main import app
        
        # 如果没有提供参数，默认执行 record 命令
        if len(sys.argv) == 1:
            sys.argv.append("record")
        
        # 运行应用
        app()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 