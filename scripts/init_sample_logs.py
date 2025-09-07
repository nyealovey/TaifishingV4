#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
泰摸鱼吧 - 初始化示例日志数据脚本
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app, db
from app.models.log import Log
from app.models.user import User

def init_sample_logs():
    """初始化示例日志数据"""
    print("📝 初始化示例日志数据...")
    
    # 创建Flask应用
    app = create_app()
    
    with app.app_context():
        # 获取用户
        users = User.query.all()
        if not users:
            print("❌ 没有找到用户，请先创建用户")
            return False
        
        # 示例日志数据
        sample_logs = [
            # 系统启动日志
            {
                'level': 'INFO',
                'log_type': 'system',
                'module': 'app',
                'message': '系统启动成功',
                'details': '泰摸鱼吧系统已成功启动，所有服务正常运行',
                'user_id': None,
                'ip_address': '127.0.0.1',
                'user_agent': 'TaifishV4/1.0.0'
            },
            {
                'level': 'INFO',
                'log_type': 'system',
                'module': 'database',
                'message': '数据库连接成功',
                'details': 'SQLite数据库连接已建立，迁移完成',
                'user_id': None,
                'ip_address': '127.0.0.1',
                'user_agent': 'TaifishV4/1.0.0'
            },
            
            # 用户操作日志
            {
                'level': 'INFO',
                'log_type': 'operation',
                'module': 'auth',
                'message': '用户登录成功',
                'details': f'用户 {users[0].username} 成功登录系统',
                'user_id': users[0].id,
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            },
            {
                'level': 'INFO',
                'log_type': 'operation',
                'module': 'instances',
                'message': '创建数据库实例',
                'details': '用户创建了新的MySQL数据库实例：test_db',
                'user_id': users[0].id,
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            },
            {
                'level': 'INFO',
                'log_type': 'operation',
                'module': 'credentials',
                'message': '创建凭据',
                'details': '用户创建了新的数据库凭据：mysql_cred',
                'user_id': users[0].id,
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            },
            {
                'level': 'WARNING',
                'log_type': 'operation',
                'module': 'instances',
                'message': '数据库连接失败',
                'details': '尝试连接数据库实例失败：连接超时',
                'user_id': users[0].id,
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            },
            {
                'level': 'ERROR',
                'log_type': 'error',
                'module': 'sync',
                'message': '数据同步失败',
                'details': '数据同步过程中发生错误：数据库连接中断',
                'user_id': users[0].id,
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            },
            {
                'level': 'INFO',
                'log_type': 'operation',
                'module': 'tasks',
                'message': '创建定时任务',
                'details': '用户创建了新的定时任务：每日数据同步',
                'user_id': users[0].id,
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            },
            {
                'level': 'INFO',
                'log_type': 'operation',
                'module': 'params',
                'message': '修改系统参数',
                'details': '用户修改了系统参数：sync_batch_size = 2000',
                'user_id': users[0].id,
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            },
            {
                'level': 'WARNING',
                'log_type': 'security',
                'module': 'auth',
                'message': '登录尝试失败',
                'details': '用户尝试使用错误密码登录：admin',
                'user_id': None,
                'ip_address': '192.168.1.200',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        ]
        
        # 生成更多随机日志
        modules = ['auth', 'instances', 'credentials', 'accounts', 'tasks', 'params', 'logs', 'sync']
        log_types = ['operation', 'system', 'error', 'security']
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
        messages = [
            '用户操作', '系统检查', '数据同步', '任务执行', '参数修改',
            '登录验证', '权限检查', '数据备份', '系统维护', '错误处理'
        ]
        
        # 生成过去7天的随机日志
        for i in range(50):
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            
            created_at = datetime.utcnow() - timedelta(
                days=days_ago, 
                hours=hours_ago, 
                minutes=minutes_ago
            )
            
            log_data = {
                'level': random.choice(levels),
                'log_type': random.choice(log_types),
                'module': random.choice(modules),
                'message': random.choice(messages),
                'details': f'这是第 {i+1} 条示例日志的详细信息',
                'user_id': random.choice(users).id if random.random() > 0.3 else None,
                'ip_address': f'192.168.1.{random.randint(100, 200)}',
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            sample_logs.append(log_data)
        
        created_count = 0
        
        for log_data in sample_logs:
            try:
                log = Log(
                    level=log_data['level'],
                    log_type=log_data['log_type'],
                    message=log_data['message'],
                    module=log_data['module'],
                    details=log_data['details'],
                    user_id=log_data['user_id'],
                    ip_address=log_data['ip_address'],
                    user_agent=log_data['user_agent']
                )
                
                # 设置创建时间
                if 'created_at' in log_data:
                    log.created_at = log_data['created_at']
                
                db.session.add(log)
                created_count += 1
                
            except Exception as e:
                print(f"  ❌ 创建日志失败: {e}")
                continue
        
        try:
            db.session.commit()
            print(f"\n🎉 示例日志数据初始化完成！")
            print(f"   创建: {created_count} 条日志")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 初始化示例日志失败: {e}")
            return False

def main():
    """主函数"""
    print("=" * 50)
    print("🐟 泰摸鱼吧 - 初始化示例日志数据")
    print("=" * 50)
    
    success = init_sample_logs()
    
    if success:
        print("\n🎉 示例日志数据设置完成！")
        print("现在可以在操作日志管理中查看这些日志")
    else:
        print("\n⚠️  示例日志数据初始化失败")
        sys.exit(1)

if __name__ == '__main__':
    main()
