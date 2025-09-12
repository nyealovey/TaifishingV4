#!/usr/bin/env python3
"""
测试所有管理页面是否正常工作
"""

import sys
from urllib.parse import urljoin

import requests

BASE_URL = "http://localhost:5001"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "Admin123"

def login():
    """登录获取session"""
    session = requests.Session()

    # 获取登录页面
    login_url = urljoin(BASE_URL, "/auth/login")
    response = session.get(login_url)

    if response.status_code != 200:
        print(f"❌ 无法访问登录页面: {response.status_code}")
        return None

    # 登录
    login_data = {
        "username": ADMIN_USER,
        "password": ADMIN_PASSWORD
    }

    response = session.post(login_url, data=login_data, allow_redirects=False)

    if response.status_code in [200, 302]:
        print(f"✅ 登录成功: {ADMIN_USER}")
        return session
    print(f"❌ 登录失败: {response.status_code}")
    return None

def test_admin_page(session, page_name, page_url):
    """测试单个管理页面"""
    full_url = urljoin(BASE_URL, page_url)

    try:
        response = session.get(full_url)

        if response.status_code == 200:
            # 检查是否包含管理布局的关键元素
            content = response.text
            if "管理中心" in content and "admin-content" in content:
                print(f"✅ {page_name}: 页面正常")
                return True
            print(f"⚠️  {page_name}: 页面加载但可能缺少管理元素")
            return False
        print(f"❌ {page_name}: HTTP {response.status_code}")
        return False

    except Exception as e:
        print(f"❌ {page_name}: 请求失败 - {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 开始测试所有管理页面...")
    print("=" * 50)

    # 登录
    session = login()
    if not session:
        print("❌ 无法登录，测试终止")
        sys.exit(1)

    # 定义所有管理页面
    admin_pages = [
        ("管理仪表板", "/admin/dashboard"),
        ("系统管理", "/admin/system-management"),
        ("性能监控", "/admin/performance"),
        ("系统日志", "/admin/logs"),
        ("错误管理", "/admin/error-management"),
        ("常量管理", "/admin/constants"),
        ("用户管理", "/admin/users"),
        ("数据管理", "/admin/data-management"),
        ("开发工具", "/admin/development-tools"),
        ("代码质量", "/admin/code-quality"),
    ]

    # 测试所有页面
    success_count = 0
    total_count = len(admin_pages)

    for page_name, page_url in admin_pages:
        if test_admin_page(session, page_name, page_url):
            success_count += 1

    print("=" * 50)
    print(f"📊 测试结果: {success_count}/{total_count} 页面正常")

    if success_count == total_count:
        print("🎉 所有管理页面都正常工作！")
        return True
    print(f"⚠️  有 {total_count - success_count} 个页面需要检查")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
