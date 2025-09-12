#!/usr/bin/env python3

"""
泰摸鱼吧 - 自动化测试运行脚本
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("test_results.log")],
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        logger.info("=" * 60)
        logger.info("泰摸鱼吧 - 自动化测试开始")
        logger.info("=" * 60)

        # 导入测试运行器
        from app.utils.test_runner import TestRunner

        # 创建测试运行器
        test_runner = TestRunner()

        # 运行所有测试
        logger.info("开始运行全面测试...")
        results = test_runner.run_all_tests()

        # 输出测试结果
        logger.info("=" * 60)
        logger.info("测试结果汇总")
        logger.info("=" * 60)

        # 单元测试结果
        unit_tests = results.get("unit_tests", {})
        logger.info(f"单元测试: {unit_tests.get('passed', 0)}/{unit_tests.get('total', 0)} 通过")

        # 集成测试结果
        integration_tests = results.get("integration_tests", {})
        logger.info(f"集成测试: {integration_tests.get('passed', 0)}/{integration_tests.get('total', 0)} 通过")

        # 性能测试结果
        performance_tests = results.get("performance_tests", {})
        logger.info(f"性能测试: {performance_tests.get('passed', 0)}/{performance_tests.get('total', 0)} 通过")

        # 安全测试结果
        security_tests = results.get("security_tests", {})
        logger.info(f"安全测试: {security_tests.get('passed', 0)}/{security_tests.get('total', 0)} 通过")

        # 总体结果
        summary = results.get("summary", {})
        logger.info(f"总测试数: {summary.get('total_tests', 0)}")
        logger.info(f"通过数: {summary.get('passed', 0)}")
        logger.info(f"失败数: {summary.get('failed', 0)}")
        logger.info(f"成功率: {summary.get('success_rate', 0):.1f}%")
        logger.info(f"执行时间: {summary.get('execution_time', 0):.2f}秒")

        # 详细结果
        logger.info("\n" + "=" * 60)
        logger.info("详细测试结果")
        logger.info("=" * 60)

        # 输出失败的测试
        for category in ["unit_tests", "integration_tests", "performance_tests", "security_tests"]:
            category_results = results.get(category, {})
            failed_tests = [r for r in category_results.get("results", []) if not r.get("success", False)]

            if failed_tests:
                logger.warning(f"\n{category.upper()} 失败测试:")
                for test in failed_tests:
                    logger.warning(f"  - {test.get('name', 'Unknown')}: {test.get('error', 'Unknown error')}")

        # 输出性能测试详情
        if performance_tests.get("results"):
            logger.info("\n性能测试详情:")
            for test in performance_tests["results"]:
                if test.get("success"):
                    execution_time = test.get("execution_time", 0)
                    logger.info(f"  - {test.get('name', 'Unknown')}: {execution_time:.3f}秒")

        # 判断测试是否成功
        if results.get("success", False) and summary.get("success_rate", 0) >= 80:
            logger.info("\n" + "=" * 60)
            logger.info("✅ 测试通过！项目质量良好")
            logger.info("=" * 60)
            return True
        logger.error("\n" + "=" * 60)
        logger.error("❌ 测试失败！需要修复问题")
        logger.error("=" * 60)
        return False

    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        import traceback

        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
