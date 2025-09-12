#!/usr/bin/env python3
"""
批量修复EM101错误：Exception must not use a string literal, assign to variable first
"""

import os
import re
from pathlib import Path

def fix_em101_errors(file_path: str) -> bool:
    """修复单个文件中的EM101错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修复模式1: raise ValueError("字符串")
        def replace_value_error(match):
            exception_type = match.group(1)
            error_msg = match.group(2)
            return f'error_msg = "{error_msg}"\n        raise {exception_type}(error_msg)'
        
        content = re.sub(
            r'(\s+)raise (ValueError|RuntimeError|ImportError|Exception)\((".*?")\s*\)',
            replace_value_error,
            content
        )
        
        # 修复模式2: raise ValueError('字符串')
        content = re.sub(
            r'(\s+)raise (ValueError|RuntimeError|ImportError|Exception)\(\'(.*?)\'\s*\)',
            lambda m: f'{m.group(1)}error_msg = \'{m.group(3)}\'\n{m.group(1)}raise {m.group(2)}(error_msg)',
            content
        )
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False

def main():
    """主函数"""
    # 需要修复的文件列表（基于ruff检查结果）
    files_to_fix = [
        "app/__init__.py",
        "app/models/user.py", 
        "app/routes/instances.py",
        "app/services/connection_factory.py",
        "app/services/database_size_service.py",
        "app/utils/retry_manager.py",
        "app/utils/validation.py"
    ]
    
    project_root = Path(__file__).parent.parent
    fixed_count = 0
    
    print("🔧 开始批量修复EM101错误...")
    print("=" * 50)
    
    for file_path in files_to_fix:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"处理文件: {file_path}")
            if fix_em101_errors(str(full_path)):
                print(f"✅ {file_path} 修复完成")
                fixed_count += 1
            else:
                print(f"ℹ️  {file_path} 无需修复")
        else:
            print(f"❌ 文件不存在: {file_path}")
    
    print("=" * 50)
    print(f"🎉 修复完成！共修复了 {fixed_count} 个文件")
    
    # 验证修复结果
    print("\n🔍 验证修复结果...")
    os.chdir(project_root)
    os.system("uv run ruff check app/ --select EM101 --no-fix")

if __name__ == "__main__":
    main()
