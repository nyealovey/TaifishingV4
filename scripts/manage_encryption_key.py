#!/usr/bin/env python3

"""
密码加密密钥管理工具
用于生成、验证和管理PASSWORD_ENCRYPTION_KEY
"""

import base64
import secrets
import sys
from pathlib import Path


def generate_key():
    """生成新的加密密钥"""
    key = secrets.token_bytes(32)
    encoded_key = base64.b64encode(key).decode("utf-8")
    return encoded_key


def validate_key(key):
    """验证密钥格式"""
    try:
        decoded = base64.b64decode(key)
        return len(decoded) == 32
    except Exception:
        return False


def update_env_file(key, env_file=".env"):
    """更新.env文件中的密钥"""
    env_path = Path(env_file)

    if not env_path.exists():
        print(f"❌ 环境文件 {env_file} 不存在")
        return False

    # 读取现有内容
    with open(env_path, encoding="utf-8") as f:
        lines = f.readlines()

    # 更新或添加密钥
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("PASSWORD_ENCRYPTION_KEY="):
            lines[i] = f"PASSWORD_ENCRYPTION_KEY={key}\n"
            updated = True
            break

    if not updated:
        lines.append(f"PASSWORD_ENCRYPTION_KEY={key}\n")

    # 写回文件
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return True


def main():
    """主函数"""
    print("🔐 密码加密密钥管理工具")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("用法:")
        print("  python manage_encryption_key.py generate  # 生成新密钥")
        print("  python manage_encryption_key.py validate <key>  # 验证密钥")
        print("  python manage_encryption_key.py update <key>  # 更新.env文件")
        return

    command = sys.argv[1]

    if command == "generate":
        key = generate_key()
        print(f"✅ 生成新密钥: {key}")
        print(f"🔧 设置环境变量: export PASSWORD_ENCRYPTION_KEY='{key}'")

        # 询问是否更新.env文件
        if input("\n是否更新.env文件? (y/N): ").lower() == "y":
            if update_env_file(key):
                print("✅ .env文件已更新")
            else:
                print("❌ 更新.env文件失败")

    elif command == "validate":
        if len(sys.argv) < 3:
            print("❌ 请提供要验证的密钥")
            return

        key = sys.argv[2]
        if validate_key(key):
            print("✅ 密钥格式正确")
        else:
            print("❌ 密钥格式错误")

    elif command == "update":
        if len(sys.argv) < 3:
            print("❌ 请提供要更新的密钥")
            return

        key = sys.argv[2]
        if not validate_key(key):
            print("❌ 密钥格式错误，请先生成有效密钥")
            return

        if update_env_file(key):
            print("✅ .env文件已更新")
        else:
            print("❌ 更新.env文件失败")

    else:
        print(f"❌ 未知命令: {command}")


if __name__ == "__main__":
    main()
