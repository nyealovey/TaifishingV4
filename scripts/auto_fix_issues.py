#!/usr/bin/env python3
"""
泰摸鱼吧 (TaifishV4) - 自动修复脚本

这个脚本用于自动修复代码质量问题，包括：
1. Ruff代码检查问题
2. Black代码格式化
3. isort导入排序
4. 部分Mypy类型检查问题
5. 部分Bandit安全问题

使用方法:
    python scripts/auto_fix_issues.py [--fix-type TYPE] [--dry-run]

参数:
    --fix-type: 指定修复类型 (all, ruff, black, isort, mypy, bandit)
    --dry-run: 只显示问题，不进行修复
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CodeFixer:
    """代码修复器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.app_dir = project_root / "app"
        self.reports_dir = project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def run_command(self, cmd: List[str], cwd: Path = None) -> subprocess.CompletedProcess:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            return result
        except Exception as e:
            logger.error(f"运行命令失败: {' '.join(cmd)} - {e}")
            return subprocess.CompletedProcess(cmd, 1, "", str(e))
    
    def fix_black_formatting(self, dry_run: bool = False) -> Dict[str, Any]:
        """修复Black格式化问题"""
        logger.info("🔍 检查Black格式化问题...")
        
        cmd = ["uv", "run", "black", "--check", "--diff", str(self.app_dir)]
        result = self.run_command(cmd)
        
        if result.returncode == 0:
            logger.info("✅ Black格式化检查通过")
            return {"status": "success", "message": "无需格式化"}
        
        if dry_run:
            logger.info("📄 发现格式化问题，但跳过修复 (dry-run模式)")
            return {"status": "dry_run", "message": "发现格式化问题"}
        
        # 执行格式化
        logger.info("🔧 执行Black格式化...")
        fix_cmd = ["uv", "run", "black", str(self.app_dir)]
        fix_result = self.run_command(fix_cmd)
        
        if fix_result.returncode == 0:
            logger.info("✅ Black格式化完成")
            return {"status": "success", "message": "格式化完成"}
        else:
            logger.error("❌ Black格式化失败")
            return {"status": "error", "message": fix_result.stderr}
    
    def fix_isort_imports(self, dry_run: bool = False) -> Dict[str, Any]:
        """修复isort导入排序问题"""
        logger.info("🔍 检查isort导入排序问题...")
        
        cmd = ["uv", "run", "isort", "--check-only", "--diff", str(self.app_dir)]
        result = self.run_command(cmd)
        
        if result.returncode == 0:
            logger.info("✅ isort导入排序检查通过")
            return {"status": "success", "message": "无需排序"}
        
        if dry_run:
            logger.info("📄 发现导入排序问题，但跳过修复 (dry-run模式)")
            return {"status": "dry_run", "message": "发现导入排序问题"}
        
        # 执行排序
        logger.info("🔧 执行isort导入排序...")
        fix_cmd = ["uv", "run", "isort", str(self.app_dir)]
        fix_result = self.run_command(fix_cmd)
        
        if fix_result.returncode == 0:
            logger.info("✅ isort导入排序完成")
            return {"status": "success", "message": "导入排序完成"}
        else:
            logger.error("❌ isort导入排序失败")
            return {"status": "error", "message": fix_result.stderr}
    
    def fix_ruff_issues(self, dry_run: bool = False) -> Dict[str, Any]:
        """修复Ruff代码检查问题"""
        logger.info("🔍 检查Ruff代码问题...")
        
        cmd = ["uv", "run", "ruff", "check", str(self.app_dir), "--output-format=json"]
        result = self.run_command(cmd)
        
        # 解析Ruff输出
        try:
            issues = json.loads(result.stdout) if result.stdout else []
        except json.JSONDecodeError:
            issues = []
        
        if not issues:
            logger.info("✅ Ruff代码检查通过")
            return {"status": "success", "message": "无代码问题"}
        
        logger.info(f"📄 发现 {len(issues)} 个Ruff问题")
        
        if dry_run:
            logger.info("📄 跳过修复 (dry-run模式)")
            return {"status": "dry_run", "message": f"发现 {len(issues)} 个问题"}
        
        # 执行自动修复
        logger.info("🔧 执行Ruff自动修复...")
        fix_cmd = ["uv", "run", "ruff", "check", str(self.app_dir), "--fix"]
        fix_result = self.run_command(fix_cmd)
        
        if fix_result.returncode == 0:
            logger.info("✅ Ruff自动修复完成")
            return {"status": "success", "message": "自动修复完成"}
        else:
            logger.warning("⚠️ Ruff自动修复部分完成，可能还有需要手动修复的问题")
            return {"status": "partial", "message": fix_result.stderr}
    
    def fix_mypy_issues(self, dry_run: bool = False) -> Dict[str, Any]:
        """修复Mypy类型检查问题"""
        logger.info("🔍 检查Mypy类型问题...")
        
        cmd = ["uv", "run", "mypy", str(self.app_dir)]
        result = self.run_command(cmd)
        
        if result.returncode == 0:
            logger.info("✅ Mypy类型检查通过")
            return {"status": "success", "message": "无类型问题"}
        
        # 统计错误数量
        error_count = result.stdout.count("error:")
        logger.info(f"📄 发现 {error_count} 个Mypy类型问题")
        
        if dry_run:
            logger.info("📄 跳过修复 (dry-run模式)")
            return {"status": "dry_run", "message": f"发现 {error_count} 个类型问题"}
        
        # Mypy没有自动修复功能，只能提供修复建议
        logger.info("💡 Mypy类型问题需要手动修复")
        logger.info("💡 建议按照错误提示添加类型注解")
        
        return {"status": "manual", "message": f"需要手动修复 {error_count} 个类型问题"}
    
    def fix_bandit_issues(self, dry_run: bool = False) -> Dict[str, Any]:
        """修复Bandit安全问题"""
        logger.info("🔍 检查Bandit安全问题...")
        
        cmd = ["uv", "run", "bandit", "-r", str(self.app_dir), "-f", "json"]
        result = self.run_command(cmd)
        
        # 解析Bandit输出
        try:
            bandit_data = json.loads(result.stdout) if result.stdout else {}
            issues = bandit_data.get("results", [])
        except json.JSONDecodeError:
            issues = []
        
        if not issues:
            logger.info("✅ Bandit安全扫描通过")
            return {"status": "success", "message": "无安全问题"}
        
        # 按严重程度分类
        high_issues = [i for i in issues if i.get("issue_severity") == "HIGH"]
        medium_issues = [i for i in issues if i.get("issue_severity") == "MEDIUM"]
        low_issues = [i for i in issues if i.get("issue_severity") == "LOW"]
        
        logger.info(f"📄 发现安全问题: 高风险 {len(high_issues)} 个, 中风险 {len(medium_issues)} 个, 低风险 {len(low_issues)} 个")
        
        if dry_run:
            logger.info("📄 跳过修复 (dry-run模式)")
            return {"status": "dry_run", "message": f"发现 {len(issues)} 个安全问题"}
        
        # Bandit没有自动修复功能，只能提供修复建议
        logger.info("💡 Bandit安全问题需要手动修复")
        logger.info("💡 建议按照安全报告修复问题")
        
        return {"status": "manual", "message": f"需要手动修复 {len(issues)} 个安全问题"}
    
    def generate_report(self, results: Dict[str, Dict[str, Any]]) -> None:
        """生成修复报告"""
        report_file = self.reports_dir / "auto_fix_report.json"
        
        report = {
            "timestamp": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], 
                                      capture_output=True, text=True).stdout.strip(),
            "results": results
        }
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 修复报告已保存到: {report_file}")
    
    def run_all_fixes(self, dry_run: bool = False) -> Dict[str, Dict[str, Any]]:
        """运行所有修复"""
        logger.info("🚀 开始自动修复代码问题...")
        logger.info("=" * 50)
        
        results = {}
        
        # 1. Black格式化
        results["black"] = self.fix_black_formatting(dry_run)
        
        # 2. isort导入排序
        results["isort"] = self.fix_isort_imports(dry_run)
        
        # 3. Ruff代码检查
        results["ruff"] = self.fix_ruff_issues(dry_run)
        
        # 4. Mypy类型检查
        results["mypy"] = self.fix_mypy_issues(dry_run)
        
        # 5. Bandit安全扫描
        results["bandit"] = self.fix_bandit_issues(dry_run)
        
        # 生成报告
        self.generate_report(results)
        
        # 显示总结
        logger.info("=" * 50)
        logger.info("📊 修复结果总结:")
        for tool, result in results.items():
            status = result["status"]
            message = result["message"]
            if status == "success":
                logger.info(f"✅ {tool.upper()}: {message}")
            elif status == "dry_run":
                logger.info(f"📄 {tool.upper()}: {message}")
            elif status == "manual":
                logger.info(f"🔧 {tool.upper()}: {message}")
            else:
                logger.error(f"❌ {tool.upper()}: {message}")
        
        return results

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="泰摸鱼吧代码自动修复工具")
    parser.add_argument(
        "--fix-type",
        choices=["all", "black", "isort", "ruff", "mypy", "bandit"],
        default="all",
        help="指定修复类型"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示问题，不进行修复"
    )
    
    args = parser.parse_args()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    fixer = CodeFixer(project_root)
    
    if args.dry_run:
        logger.info("🔍 运行模式: 只检查问题，不进行修复")
    else:
        logger.info("🔧 运行模式: 检查并修复问题")
    
    # 运行修复
    if args.fix_type == "all":
        results = fixer.run_all_fixes(args.dry_run)
    else:
        # 运行单个修复
        results = {}
        if args.fix_type == "black":
            results["black"] = fixer.fix_black_formatting(args.dry_run)
        elif args.fix_type == "isort":
            results["isort"] = fixer.fix_isort_imports(args.dry_run)
        elif args.fix_type == "ruff":
            results["ruff"] = fixer.fix_ruff_issues(args.dry_run)
        elif args.fix_type == "mypy":
            results["mypy"] = fixer.fix_mypy_issues(args.dry_run)
        elif args.fix_type == "bandit":
            results["bandit"] = fixer.fix_bandit_issues(args.dry_run)
        
        fixer.generate_report(results)
    
    # 检查是否有错误
    has_errors = any(result["status"] == "error" for result in results.values())
    if has_errors:
        logger.error("❌ 修复过程中出现错误")
        sys.exit(1)
    else:
        logger.info("✅ 修复完成")
        sys.exit(0)

if __name__ == "__main__":
    main()
