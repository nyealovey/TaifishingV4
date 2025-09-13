#!/usr/bin/env python3
"""
泰摸鱼吧 (TaifishV4) - SQL注入修复脚本

这个脚本用于修复项目中的SQL注入漏洞，将字符串拼接的SQL查询
替换为参数化查询。

使用方法:
    python scripts/fix_sql_injection.py [--dry-run] [--file FILE]

参数:
    --dry-run: 只显示问题，不进行修复
    --file: 指定要修复的文件
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SQLInjectionFixer:
    """SQL注入修复器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.app_dir = project_root / "app"

        # SQL注入模式
        self.sql_patterns = [
            # f-string SQL查询
            r'cursor\.execute\(\s*f["\']([^"\']*\{[^}]*\}[^"\']*)["\']',
            # % 格式化SQL查询
            r'cursor\.execute\(\s*["\']([^"\']*%[^"\']*)["\']\s*%',
            # .format() SQL查询
            r'cursor\.execute\(\s*["\']([^"\']*\{[^}]*\}[^"\']*)["\']\.format\(',
        ]

        # 需要修复的文件
        self.target_files = [
            "app/services/account_sync_service.py",
            "app/services/database_service.py",
        ]

    def find_sql_injection_issues(self, file_path: Path) -> list[dict[str, Any]]:
        """查找文件中的SQL注入问题"""
        issues = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return issues

        for line_num, line in enumerate(lines, 1):
            for pattern in self.sql_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    issues.append(
                        {
                            "file": str(file_path),
                            "line": line_num,
                            "content": line.strip(),
                            "pattern": pattern,
                            "match": match.group(1) if match.groups() else match.group(0),
                        }
                    )

        return issues

    def fix_sql_injection_issue(self, file_path: Path, issue: dict[str, Any]) -> str:
        """修复单个SQL注入问题"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return content

        line_num = issue["line"] - 1
        line = lines[line_num]

        # 根据不同的模式进行修复
        if 'f"' in line or "f'" in line:
            # f-string 修复
            fixed_line = self._fix_f_string_sql(line)
        elif "%" in line:
            # % 格式化修复
            fixed_line = self._fix_percent_sql(line)
        elif ".format(" in line:
            # .format() 修复
            fixed_line = self._fix_format_sql(line)
        else:
            # 其他情况，暂时跳过
            logger.warning(f"无法识别的SQL注入模式: {line}")
            return content

        if fixed_line != line:
            lines[line_num] = fixed_line
            logger.info(f"修复第 {line_num + 1} 行: {line.strip()}")
            logger.info(f"修复后: {fixed_line.strip()}")

        return "\n".join(lines)

    def _fix_f_string_sql(self, line: str) -> str:
        """修复f-string SQL查询"""
        # 提取SQL模板和变量
        # 例如: cursor.execute(f"SELECT * FROM table WHERE {condition}")
        # 修复为: cursor.execute("SELECT * FROM table WHERE %s", (condition,))

        # 简单的f-string修复逻辑
        # 这里需要根据具体情况实现更复杂的修复逻辑

        # 查找f-string中的变量
        f_string_match = re.search(r'f["\']([^"\']*\{[^}]*\}[^"\']*)["\']', line)
        if not f_string_match:
            return line

        sql_template = f_string_match.group(1)
        variables = re.findall(r"\{([^}]*)\}", sql_template)

        if not variables:
            return line

        # 构建参数化查询
        param_sql = re.sub(r"\{[^}]*\}", "%s", sql_template)
        param_tuple = ", ".join(variables)

        # 替换原始行
        new_line = line.replace(f_string_match.group(0), f'"{param_sql}", ({param_tuple},)')

        return new_line

    def _fix_percent_sql(self, line: str) -> str:
        """修复%格式化SQL查询"""
        # 例如: cursor.execute("SELECT * FROM table WHERE %s" % condition)
        # 修复为: cursor.execute("SELECT * FROM table WHERE %s", (condition,))

        # 查找%格式化的SQL
        percent_match = re.search(r'["\']([^"\']*%[^"\']*)["\']\s*%', line)
        if not percent_match:
            return line

        sql_template = percent_match.group(1)
        # 简单的修复：将 % 替换为参数化查询
        param_sql = sql_template.replace("%s", "%s")

        # 这里需要更复杂的逻辑来提取变量
        # 暂时返回原行，需要手动修复
        logger.warning(f"需要手动修复%格式化SQL: {line.strip()}")
        return line

    def _fix_format_sql(self, line: str) -> str:
        """修复.format() SQL查询"""
        # 例如: cursor.execute("SELECT * FROM table WHERE {}".format(condition))
        # 修复为: cursor.execute("SELECT * FROM table WHERE %s", (condition,))

        # 查找.format()的SQL
        format_match = re.search(r'["\']([^"\']*\{[^}]*\}[^"\']*)["\']\.format\(', line)
        if not format_match:
            return line

        sql_template = format_match.group(1)
        variables = re.findall(r"\{[^}]*\}", sql_template)

        if not variables:
            return line

        # 构建参数化查询
        param_sql = re.sub(r"\{[^}]*\}", "%s", sql_template)

        # 这里需要更复杂的逻辑来提取.format()中的参数
        # 暂时返回原行，需要手动修复
        logger.warning(f"需要手动修复.format() SQL: {line.strip()}")
        return line

    def fix_file(self, file_path: Path, dry_run: bool = False) -> dict[str, Any]:
        """修复文件中的SQL注入问题"""
        logger.info(f"🔍 检查文件: {file_path}")

        issues = self.find_sql_injection_issues(file_path)

        if not issues:
            logger.info(f"✅ {file_path} 无SQL注入问题")
            return {"status": "success", "issues": 0, "fixed": 0}

        logger.info(f"📄 发现 {len(issues)} 个SQL注入问题")

        if dry_run:
            for issue in issues:
                logger.info(f"  第 {issue['line']} 行: {issue['content']}")
            return {"status": "dry_run", "issues": len(issues), "fixed": 0}

        # 修复问题
        fixed_count = 0
        content = None

        for issue in issues:
            if content is None:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    logger.error(f"读取文件失败 {file_path}: {e}")
                    return {"status": "error", "issues": len(issues), "fixed": 0}

            new_content = self.fix_sql_injection_issue(file_path, issue)
            if new_content != content:
                content = new_content
                fixed_count += 1

        # 保存修复后的文件
        if content and fixed_count > 0:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"✅ 修复了 {fixed_count} 个SQL注入问题")
            except Exception as e:
                logger.error(f"保存文件失败 {file_path}: {e}")
                return {"status": "error", "issues": len(issues), "fixed": 0}

        return {"status": "success", "issues": len(issues), "fixed": fixed_count}

    def fix_all_files(self, dry_run: bool = False) -> dict[str, Any]:
        """修复所有目标文件"""
        logger.info("🚀 开始修复SQL注入问题...")
        logger.info("=" * 50)

        results = {}
        total_issues = 0
        total_fixed = 0

        for file_path_str in self.target_files:
            file_path = self.project_root / file_path_str
            if not file_path.exists():
                logger.warning(f"文件不存在: {file_path}")
                continue

            result = self.fix_file(file_path, dry_run)
            results[file_path_str] = result

            total_issues += result["issues"]
            total_fixed += result["fixed"]

        # 显示总结
        logger.info("=" * 50)
        logger.info("📊 SQL注入修复结果总结:")
        logger.info(f"   总问题数: {total_issues}")
        logger.info(f"   修复数量: {total_fixed}")

        for file_path, result in results.items():
            status = result["status"]
            issues = result["issues"]
            fixed = result["fixed"]

            if status == "success":
                logger.info(f"✅ {file_path}: {issues} 个问题, 修复了 {fixed} 个")
            elif status == "dry_run":
                logger.info(f"📄 {file_path}: {issues} 个问题 (dry-run模式)")
            else:
                logger.error(f"❌ {file_path}: 修复失败")

        return {"total_issues": total_issues, "total_fixed": total_fixed, "files": results}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="泰摸鱼吧SQL注入修复工具")
    parser.add_argument("--dry-run", action="store_true", help="只显示问题，不进行修复")
    parser.add_argument("--file", help="指定要修复的文件")

    args = parser.parse_args()

    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    fixer = SQLInjectionFixer(project_root)

    if args.dry_run:
        logger.info("🔍 运行模式: 只检查问题，不进行修复")
    else:
        logger.info("🔧 运行模式: 检查并修复问题")

    # 运行修复
    if args.file:
        file_path = project_root / args.file
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            sys.exit(1)

        result = fixer.fix_file(file_path, args.dry_run)
        if result["status"] == "error":
            sys.exit(1)
    else:
        result = fixer.fix_all_files(args.dry_run)
        if result["total_fixed"] == 0 and not args.dry_run:
            logger.warning("⚠️ 没有修复任何问题，可能需要手动修复")

    logger.info("✅ SQL注入修复完成")
    sys.exit(0)


if __name__ == "__main__":
    main()
