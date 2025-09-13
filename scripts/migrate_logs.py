#!/usr/bin/env python3
"""
批量迁移日志调用到structlog模式
"""

import re
from pathlib import Path


def migrate_log_calls(file_path: Path):
    """迁移单个文件的日志调用"""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # 替换log_operation调用
        content = re.sub(
            r'log_operation\(\s*"([^"]+)",\s*([^,]+),\s*\{([^}]+)\}\s*\)',
            r'api_logger.info("\1", user_id=\2, \3)',
            content,
            flags=re.MULTILINE | re.DOTALL,
        )

        # 替换简单的log_operation调用
        content = re.sub(r'log_operation\(\s*"([^"]+)",\s*([^,]+)\s*\)', r'api_logger.info("\1", user_id=\2)', content)

        # 替换log_error调用
        content = re.sub(r'log_error\(\s*"([^"]+)",\s*([^,]+)\s*\)', r'log_error("\1", exception=\2)', content)

        # 替换log_info调用
        content = re.sub(r'log_info\(\s*"([^"]+)"\s*\)', r'log_info("\1")', content)

        # 替换log_warning调用
        content = re.sub(r'log_warning\(\s*"([^"]+)"\s*\)', r'log_warning("\1")', content)

        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ 迁移完成: {file_path}")
            return True
        print(f"⏭️  无需迁移: {file_path}")
        return False

    except Exception as e:
        print(f"❌ 迁移失败 {file_path}: {e}")
        return False


def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    app_dir = project_root / "app"

    # 需要迁移的文件列表
    files_to_migrate = [
        "routes/instances.py",
        "routes/credentials.py",
        "routes/account_classification.py",
        "routes/account_list.py",
        "routes/account_sync.py",
        "routes/account_static.py",
        "routes/dashboard.py",
        "routes/health.py",
        "routes/logs.py",
        "routes/main.py",
        "routes/scheduler.py",
        "routes/user_management.py",
        "routes/admin.py",
        "routes/database_types.py",
        "services/connection_factory.py",
        "services/task_executor.py",
        "services/account_classification_service.py",
        "services/database_type_service.py",
        "services/database_size_service.py",
        "services/permission_query_factory.py",
        "utils/error_handler.py",
        "utils/advanced_error_handler.py",
        "utils/cache_manager.py",
        "utils/rate_limiter.py",
        "utils/retry_manager.py",
        "utils/password_manager.py",
        "utils/env_validator.py",
        "utils/db_context.py",
        "middleware/error_logging_middleware.py",
        "tasks.py",
        "scheduler.py",
    ]

    print("🚀 开始批量迁移日志调用...")
    print("=" * 50)

    migrated_count = 0
    total_count = len(files_to_migrate)

    for file_path in files_to_migrate:
        full_path = app_dir / file_path
        if full_path.exists():
            if migrate_log_calls(full_path):
                migrated_count += 1
        else:
            print(f"⚠️  文件不存在: {file_path}")

    print("=" * 50)
    print("📊 迁移统计:")
    print(f"   总文件数: {total_count}")
    print(f"   成功迁移: {migrated_count}")
    print(f"   跳过文件: {total_count - migrated_count}")


if __name__ == "__main__":
    main()
