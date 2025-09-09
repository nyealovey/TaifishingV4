#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
启动Celery Beat调度器
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault('FLASK_APP', 'app')
os.environ.setdefault('FLASK_ENV', 'development')

from app.celery_config import celery

if __name__ == '__main__':
    # 启动Celery Beat
    celery.start(['beat', '--loglevel=info'])
