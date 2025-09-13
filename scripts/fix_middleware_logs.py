#!/usr/bin/env python3
"""
修复middleware中的日志调用
"""

import re
from pathlib import Path


def fix_middleware_logs():
    """修复middleware中的日志调用"""
    file_path = Path("app/middleware/error_logging_middleware.py")

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # 替换log_exception调用
    content = re.sub(
        r'log_exception\(([^,]+),\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)',
        r'log_error("\2", exception=\1, module="\3", level="\4")',
        content,
    )

    # 替换enhanced_logger调用
    content = re.sub(
        r'enhanced_logger\.critical\(f"([^"]+)",\s*"([^"]+)"\)', r'log_critical("\1", module="\2")', content
    )

    # 替换enhanced_logger.info调用
    content = re.sub(r'enhanced_logger\.info\(f"([^"]+)",\s*"([^"]+)"\)', r'log_info("\1", module="\2")', content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ 修复middleware日志调用完成")


if __name__ == "__main__":
    fix_middleware_logs()
