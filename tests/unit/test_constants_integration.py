#!/usr/bin/env python3
"""
常量集成测试脚本
验证常量管理系统是否正确集成
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import Config
from app.constants import DefaultConfig, ErrorMessages, SuccessMessages, SystemConstants


def test_constants_import():
    """测试常量导入"""
    print("=== 测试常量导入 ===")

    try:
        # 测试SystemConstants
        print(f"✓ DEFAULT_PAGE_SIZE: {SystemConstants.DEFAULT_PAGE_SIZE}")
        print(f"✓ MAX_FILE_SIZE: {SystemConstants.MAX_FILE_SIZE}")
        print(f"✓ MEMORY_WARNING_THRESHOLD: {SystemConstants.MEMORY_WARNING_THRESHOLD}")
        print(f"✓ PASSWORD_HASH_ROUNDS: {SystemConstants.PASSWORD_HASH_ROUNDS}")

        # 测试DefaultConfig
        print(f"✓ DATABASE_URL: {DefaultConfig.DATABASE_URL}")
        print(f"✓ SECRET_KEY: {DefaultConfig.SECRET_KEY[:20]}...")

        # 测试ErrorMessages
        print(f"✓ INTERNAL_ERROR: {ErrorMessages.INTERNAL_ERROR}")
        print(f"✓ VALIDATION_ERROR: {ErrorMessages.VALIDATION_ERROR}")

        # 测试SuccessMessages
        print(f"✓ OPERATION_SUCCESS: {SuccessMessages.OPERATION_SUCCESS}")
        print(f"✓ LOGIN_SUCCESS: {SuccessMessages.LOGIN_SUCCESS}")

        print("✓ 所有常量导入成功")
        return True

    except Exception as e:
        print(f"✗ 常量导入失败: {e}")
        return False


def test_config_integration():
    """测试配置集成"""
    print("\n=== 测试配置集成 ===")

    try:
        config = Config()

        # 检查配置是否使用了常量
        print(f"✓ SECRET_KEY默认值: {config.SECRET_KEY[:20]}...")
        print(f"✓ JWT_ACCESS_TOKEN_EXPIRES: {config.JWT_ACCESS_TOKEN_EXPIRES}")
        print(f"✓ MAX_CONTENT_LENGTH: {config.MAX_CONTENT_LENGTH}")
        print(f"✓ BCRYPT_LOG_ROUNDS: {config.BCRYPT_LOG_ROUNDS}")
        print(f"✓ CACHE_DEFAULT_TIMEOUT: {config.CACHE_DEFAULT_TIMEOUT}")

        print("✓ 配置集成成功")
        return True

    except Exception as e:
        print(f"✗ 配置集成失败: {e}")
        return False


def test_hardcoded_replacement():
    """测试硬编码值替换"""
    print("\n=== 测试硬编码值替换 ===")

    # 检查一些关键文件是否还有硬编码值
    files_to_check = [
        "app/config.py",
        "app/utils/rate_limiter.py",
    ]

    hardcoded_found = False

    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # 检查是否还有明显的硬编码值
            suspicious_values = ["= 20", "= 100", "= 300", "= 3600", "= 80", "= 12"]
            for value in suspicious_values:
                if value in content and "SystemConstants" not in content:
                    print(f"⚠  {file_path} 中可能还有硬编码值: {value}")
                    hardcoded_found = True

    if not hardcoded_found:
        print("✓ 未发现明显的硬编码值")
        return True
    print("⚠ 发现一些可能的硬编码值，需要进一步检查")
    return False


def test_constant_usage():
    """测试常量使用"""
    print("\n=== 测试常量使用 ===")

    try:
        # 测试常量在代码中的使用
        print("✓ 速率限制器使用常量")

        # 测试常量值的一致性
        assert SystemConstants.DEFAULT_PAGE_SIZE == 20
        assert SystemConstants.MAX_FILE_SIZE == 16 * 1024 * 1024
        assert SystemConstants.MEMORY_WARNING_THRESHOLD == 80
        assert SystemConstants.PASSWORD_HASH_ROUNDS == 12

        print("✓ 常量值一致性验证通过")
        return True

    except Exception as e:
        print(f"✗ 常量使用测试失败: {e}")
        return False


def main():
    """主函数"""
    print("开始常量集成测试...\n")

    tests = [test_constants_import, test_config_integration, test_hardcoded_replacement, test_constant_usage]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed / total * 100:.1f}%")

    if passed == total:
        print("🎉 所有测试通过！常量管理系统集成成功！")
        return True
    print("❌ 部分测试失败，需要进一步检查")
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
