#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复日志记录缺失问题
"""

import os
import re
from pathlib import Path

def add_logging_to_route(file_path, route_pattern):
    """为路由添加日志记录"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经有日志导入
    if 'from app.utils.logger import log_operation, log_api_request' not in content:
        # 添加日志导入
        import_pattern = r'(from flask import.*?\n)'
        match = re.search(import_pattern, content)
        if match:
            content = content.replace(
                match.group(1),
                match.group(1) + 'from app.utils.logger import log_operation, log_api_request\n'
            )
    
    # 为API路由添加日志记录
    def add_logging_to_function(match):
        function_def = match.group(0)
        function_name = match.group(1)
        route_path = match.group(2)
        
        # 检查是否已经有日志记录
        if 'log_api_request' in function_def or 'log_operation' in function_def:
            return function_def
        
        # 添加日志记录
        if '/api/' in route_path:
            # API路由
            logging_code = f'''
    import time
    start_time = time.time()
    
    # 原有代码...
    
    # 记录API调用
    duration = (time.time() - start_time) * 1000
    user_id = get_jwt_identity() if 'jwt_required' in function_def else current_user.id if 'login_required' in function_def else None
    log_api_request('GET', '{route_path}', 200, duration, user_id, request.remote_addr)
'''
        else:
            # 普通路由
            logging_code = f'''
    import time
    start_time = time.time()
    
    # 原有代码...
    
    # 记录操作日志
    duration = (time.time() - start_time) * 1000
    if current_user.is_authenticated:
        log_operation('{function_name.upper()}', current_user.id, {{
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'duration_ms': duration
        }})
'''
        
        return function_def.replace('def ' + function_name + '():', 'def ' + function_name + '():' + logging_code)
    
    # 匹配函数定义
    pattern = r'@\w+\.route\([\'"]([^\'"]+)[\'"].*?\n.*?def (\w+)\([^)]*\):'
    content = re.sub(pattern, add_logging_to_function, content, flags=re.MULTILINE | re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"已处理文件: {file_path}")

def main():
    """主函数"""
    routes_dir = Path('app/routes')
    
    # 需要处理的文件
    files_to_process = [
        'dashboard.py',
        'instances.py', 
        'credentials.py',
        'accounts.py',
        'tasks.py',
        'logs.py',
        'params.py',
        'main.py'
    ]
    
    for file_name in files_to_process:
        file_path = routes_dir / file_name
        if file_path.exists():
            print(f"处理文件: {file_name}")
            add_logging_to_route(file_path, None)
        else:
            print(f"文件不存在: {file_name}")

if __name__ == '__main__':
    main()
