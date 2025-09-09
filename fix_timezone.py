#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复时区问题脚本
将所有datetime.utcnow()替换为统一的时区管理函数
"""

import os
import re
from pathlib import Path

def fix_file_timezone(file_path):
    """修复单个文件的时区问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 替换datetime.utcnow()为now()
        content = re.sub(r'datetime\.utcnow\(\)', 'now()', content)
        
        # 如果文件被修改了，需要添加导入
        if content != original_content:
            # 检查是否已经有timezone导入
            if 'from app.utils.timezone import' not in content:
                # 找到第一个import语句的位置
                import_match = re.search(r'^from datetime import.*$', content, re.MULTILINE)
                if import_match:
                    # 在datetime导入后添加timezone导入
                    insert_pos = import_match.end()
                    content = content[:insert_pos] + '\nfrom app.utils.timezone import now' + content[insert_pos:]
                else:
                    # 如果没有找到datetime导入，在文件开头添加
                    content = 'from app.utils.timezone import now\n' + content
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 修复文件: {file_path}")
            return True
        else:
            print(f"⏭️  跳过文件: {file_path} (无需修改)")
            return False
            
    except Exception as e:
        print(f"❌ 修复文件失败: {file_path}, 错误: {e}")
        return False

def main():
    """主函数"""
    print("🔧 开始修复时区问题...")
    
    # 需要修复的文件类型
    file_extensions = ['.py']
    
    # 需要跳过的目录
    skip_dirs = {'venv', '__pycache__', '.git', 'migrations', 'node_modules'}
    
    # 需要跳过的文件
    skip_files = {'fix_timezone.py', 'debug_timezone.py', 'test_timezone.py', 'test_china_time.py'}
    
    fixed_count = 0
    total_count = 0
    
    # 遍历项目目录
    for root, dirs, files in os.walk('.'):
        # 跳过不需要的目录
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            file_path = Path(root) / file
            
            # 跳过不需要的文件
            if file in skip_files:
                continue
                
            # 只处理Python文件
            if file_path.suffix in file_extensions:
                total_count += 1
                if fix_file_timezone(file_path):
                    fixed_count += 1
    
    print(f"\n📊 修复完成:")
    print(f"   总文件数: {total_count}")
    print(f"   修复文件数: {fixed_count}")
    print(f"   跳过文件数: {total_count - fixed_count}")

if __name__ == '__main__':
    main()
