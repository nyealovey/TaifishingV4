#!/usr/bin/env python3
"""
代码质量检查脚本
快速运行所有质量检查工具
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd: list[str], description: str, output_file: str = None) -> tuple[bool, str]:
    """运行命令并返回结果"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        if result.returncode == 0:
            print(f"✅ {description} 通过")
            # 如果指定了输出文件，保存结果
            if output_file:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(result.stdout)
                print(f"📄 报告已保存到: {output_file}")
            return True, result.stdout
        print(f"❌ {description} 失败")
        print(f"错误: {result.stderr}")
        # 即使失败也保存输出文件
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"错误: {result.stderr}\n\n标准输出:\n{result.stdout}")
            print(f"📄 错误报告已保存到: {output_file}")
        return False, result.stderr
    except Exception as e:
        print(f"❌ {description} 执行失败: {e}")
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"执行失败: {e}")
            print(f"📄 错误报告已保存到: {output_file}")
        return False, str(e)


def main():
    """主函数"""
    print("🚀 开始代码质量检查...")
    print("=" * 50)

    # 创建报告目录
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)

    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
    black_report = report_dir / f"black-report_{timestamp}.txt"
    success, output = run_command(
        ["uv", "run", "black", "app/", "--check", "--diff"], "Black 代码格式化检查", str(black_report)
    )
    results.append(("Black", success))

    # 2. isort 导入排序检查
    isort_report = report_dir / f"isort-report_{timestamp}.txt"
    success, output = run_command(
        ["uv", "run", "isort", "app/", "--check-only", "--diff"], "isort 导入排序检查", str(isort_report)
    )
    results.append(("isort", success))

    # 3. Ruff 代码检查
    ruff_report = report_dir / f"ruff-report_{timestamp}.json"
    success, output = run_command(
        ["uv", "run", "ruff", "check", "app/", "--output-format=json"], "Ruff 代码检查", str(ruff_report)
    )
    results.append(("Ruff", success))

    # 4. Mypy 类型检查
    mypy_report = report_dir / f"mypy-report_{timestamp}.txt"
    success, output = run_command(["uv", "run", "mypy", "app/"], "Mypy 类型检查", str(mypy_report))
    results.append(("Mypy", success))

    # 5. Bandit 安全扫描
    bandit_report = report_dir / f"bandit-report_{timestamp}.json"
    success, output = run_command(
        ["uv", "run", "bandit", "-r", "app/", "-f", "json", "-o", str(bandit_report)], "Bandit 安全扫描"
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

    # 显示生成的报告文件
    print("\n📄 生成的报告文件:")
    print("=" * 50)
    report_files = [black_report, isort_report, ruff_report, mypy_report, bandit_report]

    for report_file in report_files:
        if report_file.exists():
            size = report_file.stat().st_size
            print(f"✅ {report_file.name} ({size} bytes)")
        else:
            print(f"❌ {report_file.name} (未生成)")

    print(f"\n📁 报告目录: {report_dir.absolute()}")

    if failed > 0:
        print("\n💡 修复建议:")
        print("1. 运行 'uv run black app/' 格式化代码")
        print("2. 运行 'uv run isort app/' 排序导入")
        print("3. 运行 'uv run ruff check app/ --fix' 自动修复问题")
        print("4. 手动修复 Mypy 类型检查问题")
        print("5. 查看生成的报告文件了解详细问题")
        sys.exit(1)
    else:
        print("\n🎉 所有检查都通过了！代码质量良好！")
        sys.exit(0)


if __name__ == "__main__":
    main()
