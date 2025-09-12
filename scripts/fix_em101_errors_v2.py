#!/usr/bin/env python3
"""
批量修复EM101错误：Exception must not use a string literal, assign to variable first
更精确的修复方法
"""

import os
import re
from pathlib import Path

def fix_em101_errors(file_path: str) -> bool:
    """修复单个文件中的EM101错误"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        original_lines = lines.copy()
        modified = False
        
        for i, line in enumerate(lines):
            # 匹配 raise Exception("字符串") 或 raise Exception('字符串')
            match = re.match(r'^(\s+)raise (ValueError|RuntimeError|ImportError|Exception)\((["\'])(.*?)\3\s*\)$', line)
            if match:
                indent = match.group(1)
                exception_type = match.group(2)
                quote_char = match.group(3)
                error_msg = match.group(4)
                
                # 替换为两行：先赋值，再raise
                new_lines = [
                    f'{indent}error_msg = {quote_char}{error_msg}{quote_char}\n',
                    f'{indent}raise {exception_type}(error_msg)\n'
                ]
                
                lines[i:i+1] = new_lines
                modified = True
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
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
