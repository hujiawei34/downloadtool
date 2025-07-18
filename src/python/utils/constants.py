#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目常量定义
"""

from pathlib import Path

# 项目根目录 - 从当前文件向上3级
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


# 重要路径
REQUIREMENTS_FILE = PROJECT_ROOT / "src" / "python" / "requirements.txt"
CONFIG_FILE = PROJECT_ROOT / "config.json"

FRONT_DIR = PROJECT_ROOT / "front"

# 日志文件路径
LOG_FILE = PROJECT_ROOT / "logs" / "app.log"