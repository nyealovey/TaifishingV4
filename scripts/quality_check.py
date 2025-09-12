#!/usr/bin/env python3
"""
代码质量检查脚本
快速运行所有质量检查工具
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str], description: str) -> Tuple[bool, str]:
    """运行命令并返回结果"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            print(f"✅ {description} 通过")
            return True, result.stdout
        else:
            print(f"❌ {description} 失败")
            print(f"错误: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description} 执行失败: {e}")
        return False, str(e)


def main():
    """主函数"""
    print("🚀 开始代码质量检查...")
    print("=" * 50)
    
    # 检查工具是否安装
    tools = ["ruff", "mypy", "bandit", "black", "isort"]
    for tool in tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ 工具 {tool} 未安装，请运行: uv sync --dev")
            sys.exit(1)
    
    # 检查结果
    results = []
    
    # 1. Black 格式化检查
    success, output = run_command(
        ["uv", "run", "black", "app/", "--check", "--diff"],
        "Black 代码格式化检查"
    )
    results.append(("Black", success))
    
    # 2. isort 导入排序检查
    success, output = run_command(
        ["uv", "run", "isort", "app/", "--check-only", "--diff"],
        "isort 导入排序检查"
    )
    results.append(("isort", success))
    
    # 3. Ruff 代码检查
    success, output = run_command(
        ["uv", "run", "ruff", "check", "app/"],
        "Ruff 代码检查"
    )
    results.append(("Ruff", success))
    
    # 4. Mypy 类型检查
    success, output = run_command(
        ["uv", "run", "mypy", "app/"],
        "Mypy 类型检查"
    )
    results.append(("Mypy", success))
    
    # 5. Bandit 安全扫描
    success, output = run_command(
        ["uv", "run", "bandit", "-r", "app/", "-f", "json", "-o", "bandit-report.json"],
        "Bandit 安全扫描"
    )
    results.append(("Bandit", success))
    
    # 输出结果摘要
    print("\n" + "=" * 50)
    print("📊 检查结果摘要:")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for tool, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{tool:10} {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print("=" * 50)
    print(f"总计: {passed + failed}, 通过: {passed}, 失败: {failed}")
    
    if failed > 0:
        print("\n💡 修复建议:")
        print("1. 运行 'uv run black app/' 格式化代码")
        print("2. 运行 'uv run isort app/' 排序导入")
        print("3. 运行 'uv run ruff check app/ --fix' 自动修复问题")
        print("4. 手动修复 Mypy 类型检查问题")
        print("5. 查看 bandit-report.json 了解安全问题")
        sys.exit(1)
    else:
        print("\n🎉 所有检查都通过了！代码质量良好！")
        sys.exit(0)


if __name__ == "__main__":
    main()
