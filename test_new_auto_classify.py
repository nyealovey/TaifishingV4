#!/usr/bin/env python3
"""
测试新的自动分类逻辑
验证只有分类变化时才更新账户记录
"""

import requests


def test_auto_classify():
    """测试自动分类功能"""
    base_url = "http://localhost:5001"

    # 创建会话
    session = requests.Session()

    try:
        # 1. 获取登录页面获取CSRF token
        print("1. 获取登录页面...")
        login_page = session.get(f"{base_url}/login")
        if login_page.status_code != 200:
            print(f"❌ 无法访问登录页面: {login_page.status_code}")
            return

        # 2. 登录获取认证
        print("2. 登录...")
        login_data = {"username": "admin", "password": "admin123"}
        login_response = session.post(f"{base_url}/login", data=login_data)
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            return

        # 3. 获取自动分类页面获取CSRF token
        print("3. 获取自动分类页面...")
        classify_page = session.get(f"{base_url}/account-classification/")
        if classify_page.status_code != 200:
            print(f"❌ 无法访问自动分类页面: {classify_page.status_code}")
            return

        # 4. 执行自动分类
        print("4. 执行自动分类...")
        auto_classify_data = {"instance_id": ""}
        auto_classify_response = session.post(
            f"{base_url}/account-classification/auto-classify", data=auto_classify_data
        )

        print(f"自动分类响应状态: {auto_classify_response.status_code}")
        print(f"自动分类响应内容: {auto_classify_response.text}")

        if auto_classify_response.status_code == 200:
            result = auto_classify_response.json()
            if result.get("success"):
                print("✅ 自动分类执行成功")
                print(f"批次ID: {result.get('batch_id')}")
                print(f"匹配账户数: {result.get('classified_accounts')}")
                print(f"总匹配次数: {result.get('total_matches')}")

                # 5. 检查数据库中的账户记录
                print("\n5. 检查账户分类记录...")
                check_accounts_with_classification(session, result.get("batch_id"))
            else:
                print(f"❌ 自动分类失败: {result.get('error')}")
        else:
            print(f"❌ 自动分类请求失败: {auto_classify_response.status_code}")

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")


def check_accounts_with_classification(session, batch_id):
    """检查有分类记录的账户"""
    try:
        # 获取批次详情
        batch_response = session.get(f"http://localhost:5001/account-classification/api/batches/{batch_id}")
        if batch_response.status_code == 200:
            batch_data = batch_response.json()
            print(f"批次状态: {batch_data.get('status')}")
            print(f"匹配账户数: {batch_data.get('matched_accounts')}")
            print(f"总账户数: {batch_data.get('total_accounts')}")

            # 获取匹配详情
            matches_response = session.get(
                f"http://localhost:5001/account-classification/api/batches/{batch_id}/matches"
            )
            if matches_response.status_code == 200:
                matches_data = matches_response.json()
                print(f"\n匹配详情记录数: {len(matches_data.get('matches', []))}")

                # 显示前几个匹配记录
                for i, match in enumerate(matches_data.get("matches", [])[:5]):
                    print(
                        f"  {i + 1}. 账户: {match.get('account_name')} | 实例: {match.get('instance_name')} | 分类: {match.get('classification_name')}"
                    )
        else:
            print(f"❌ 无法获取批次详情: {batch_response.status_code}")

    except Exception as e:
        print(f"❌ 检查账户分类记录时发生错误: {e}")


if __name__ == "__main__":
    print("开始测试新的自动分类逻辑...")
    print("=" * 50)
    test_auto_classify()
    print("=" * 50)
    print("测试完成")
