#!/usr/bin/env python3
"""
泰摸鱼吧 - 日志系统迁移脚本
将现有的日志系统迁移到Loguru
"""

import re
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class LogMigrationTool:
    """日志迁移工具"""

    def __init__(self):
        self.project_root = project_root
        self.app_dir = project_root / "app"
        self.migration_stats = {"files_processed": 0, "replacements_made": 0, "errors": []}

    def find_python_files(self) -> list[Path]:
        """查找所有Python文件"""
        python_files = []
        for file_path in self.app_dir.rglob("*.py"):
            if file_path.name != "__pycache__":
                python_files.append(file_path)
        return python_files

    def get_logging_patterns(self) -> dict[str, str]:
        """获取日志替换模式"""
        return {
            # 标准logging替换
            r"logging\.(debug|info|warning|error|critical)\(([^)]+)\)": r"log_\1(\2)",
            # logger替换
            r"logger\.(debug|info|warning|error|critical)\(([^)]+)\)": r"log_\1(\2)",
            # enhanced_logger替换
            r"enhanced_logger\.(debug|info|warning|error|critical)\(([^)]+)\)": r"log_\1(\2)",
            # 专用logger替换
            r"(auth_logger|db_logger|sync_logger|api_logger|security_logger|system_logger)\.(debug|info|warning|error|critical)\(([^)]+)\)": r"log_\2(\3)",
            # log_operation替换
            r"log_operation\(([^)]+)\)": r"log_info(\1)",
            # log_error替换
            r"log_error\(([^)]+)\)": r"log_error(\1)",
            # log_exception替换
            r"log_exception\(([^)]+)\)": r"log_error(\1)",
        }

    def migrate_file(self, file_path: Path) -> bool:
        """迁移单个文件"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # 添加导入语句
            if "from app.utils.loguru_logging_system import" not in content:
                # 找到最后一个import语句
                import_lines = []
                other_lines = []
                in_imports = True

                for line in content.split("\n"):
                    if in_imports and (line.startswith("import ") or line.startswith("from ")):
                        import_lines.append(line)
                    else:
                        in_imports = False
                        other_lines.append(line)

                # 添加新的import
                import_lines.append("from app.utils.loguru_logging_system import *")

                # 重新组合内容
                content = "\n".join(import_lines + other_lines)

            # 应用替换模式
            patterns = self.get_logging_patterns()
            for pattern, replacement in patterns.items():
                content = re.sub(pattern, replacement, content)

            # 如果内容有变化，写回文件
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                self.migration_stats["replacements_made"] += 1
                print(f"✅ 迁移完成: {file_path.relative_to(self.project_root)}")
                return True
            print(f"⏭️  无需迁移: {file_path.relative_to(self.project_root)}")
            return False

        except Exception as e:
            error_msg = f"迁移文件失败 {file_path}: {e}"
            self.migration_stats["errors"].append(error_msg)
            print(f"❌ {error_msg}")
            return False

    def migrate_all_files(self) -> None:
        """迁移所有文件"""
        print("🚀 开始迁移日志系统到Loguru...")
        print("=" * 50)

        python_files = self.find_python_files()
        print(f"📁 找到 {len(python_files)} 个Python文件")

        for file_path in python_files:
            self.migration_stats["files_processed"] += 1
            self.migrate_file(file_path)

        print("=" * 50)
        print("📊 迁移统计:")
        print(f"   处理文件数: {self.migration_stats['files_processed']}")
        print(f"   成功迁移: {self.migration_stats['replacements_made']}")
        print(f"   错误数量: {len(self.migration_stats['errors'])}")

        if self.migration_stats["errors"]:
            print("\n❌ 错误详情:")
            for error in self.migration_stats["errors"]:
                print(f"   {error}")

    def create_migration_guide(self) -> None:
        """创建迁移指南"""
        guide_content = """
# Loguru日志系统迁移指南

## 迁移完成后的使用方式

### 1. 基础日志记录
```python
from app.utils.loguru_logging_system import *

# 基础日志
log_info("这是一条信息日志")
log_warning("这是一条警告日志")
log_error("这是一条错误日志")
log_debug("这是一条调试日志")
log_critical("这是一条严重错误日志")
```

### 2. 带上下文的日志
```python
# 带额外信息
log_info("用户登录", user_id=123, action="login")
log_error("数据库连接失败", database="mysql", error=str(e))
```

### 3. 分类日志
```python
# 访问日志
log_access("API请求", endpoint="/api/users", method="GET")

# 安全日志
log_security("登录失败", user_id=123, ip="192.168.1.1")

# 数据库日志
log_database("查询执行", query="SELECT * FROM users", duration=0.5)

# 任务日志
log_task("同步完成", task_id=1, records=100)
```

### 4. 结构化日志
```python
# 结构化日志
log_structured("user_action", {
    "user_id": 123,
    "action": "login",
    "timestamp": "2024-01-01T00:00:00Z",
    "ip_address": "192.168.1.1"
})
```

### 5. 装饰器使用
```python
from app.utils.loguru_logging_system import log_function_call, log_database_operation

@log_function_call
def my_function():
    pass

@log_database_operation("SELECT")
def query_database():
    pass
```

## 日志文件说明

- `app.log`: 应用主日志
- `error.log`: 错误日志
- `access.log`: 访问日志
- `security.log`: 安全日志
- `database.log`: 数据库日志
- `tasks.log`: 任务日志
- `structured.log`: 结构化日志（JSON格式）

## 配置说明

日志配置通过环境变量控制：

- `LOG_LEVEL`: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_DIR`: 日志目录
- `LOG_MAX_FILE_SIZE`: 最大文件大小
- `LOG_RETENTION_DAYS`: 日志保留天数

## 日志分析

使用内置的日志分析工具：

```python
from app.utils.log_analyzer import analyze_logs, get_error_summary

# 分析日志
stats = analyze_logs("app", days=7)
print(f"总日志数: {stats.total_logs}")
print(f"错误数: {stats.error_count}")

# 获取错误摘要
error_summary = get_error_summary(days=1)
print(f"今日错误: {error_summary['error_count']}")
```
"""

        guide_file = self.project_root / "docs" / "development" / "LOGURU_MIGRATION_GUIDE.md"
        guide_file.parent.mkdir(parents=True, exist_ok=True)

        with open(guide_file, "w", encoding="utf-8") as f:
            f.write(guide_content)

        print(f"📖 迁移指南已创建: {guide_file}")


def main():
    """主函数"""
    print("🔧 泰摸鱼吧日志系统迁移工具")
    print("将现有日志系统迁移到Loguru")
    print()

    # 确认迁移
    confirm = input("是否继续迁移? (y/N): ").lower().strip()
    if confirm != "y":
        print("❌ 迁移已取消")
        return

    # 创建迁移工具
    migration_tool = LogMigrationTool()

    # 执行迁移
    migration_tool.migrate_all_files()

    # 创建迁移指南
    migration_tool.create_migration_guide()

    print("\n🎉 迁移完成!")
    print("请查看迁移指南了解新的使用方式")


if __name__ == "__main__":
    main()
