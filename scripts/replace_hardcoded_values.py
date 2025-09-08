#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硬编码值替换脚本
自动替换代码中的魔法数字和硬编码值
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple

class HardcodedValueReplacer:
    """硬编码值替换器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.replacements = self._load_replacement_mapping()
        self.stats = {
            'files_processed': 0,
            'replacements_made': 0,
            'errors': 0
        }
    
    def _load_replacement_mapping(self) -> Dict[str, str]:
        """加载替换映射"""
        return {
            # 分页相关
            r'\b20\b(?=\s*#.*分页|\s*#.*page)': 'SystemConstants.DEFAULT_PAGE_SIZE',
            r'\b100\b(?=\s*#.*最大|\s*#.*max)': 'SystemConstants.MAX_PAGE_SIZE',
            r'\b1\b(?=\s*#.*最小|\s*#.*min)': 'SystemConstants.MIN_PAGE_SIZE',
            
            # 时间相关
            r'\b300\b(?=\s*#.*秒|\s*#.*second)': 'SystemConstants.DEFAULT_CACHE_TIMEOUT',
            r'\b3600\b(?=\s*#.*小时|\s*#.*hour)': 'SystemConstants.SESSION_LIFETIME',
            r'\b60\b(?=\s*#.*分钟|\s*#.*minute)': 'SystemConstants.SHORT_CACHE_TIMEOUT',
            
            # 文件大小相关
            r'\b16777216\b(?=\s*#.*MB|\s*#.*file)': 'SystemConstants.MAX_FILE_SIZE',
            r'\b10485760\b(?=\s*#.*MB|\s*#.*log)': 'SystemConstants.LOG_MAX_SIZE',
            
            # 安全相关
            r'\b12\b(?=\s*#.*轮|\s*#.*round)': 'SystemConstants.PASSWORD_HASH_ROUNDS',
            r'\b8\b(?=\s*#.*密码|\s*#.*password)': 'SystemConstants.MIN_PASSWORD_LENGTH',
            r'\b128\b(?=\s*#.*密码|\s*#.*password)': 'SystemConstants.MAX_PASSWORD_LENGTH',
            
            # 性能相关
            r'\b80\b(?=\s*#.*内存|\s*#.*memory)': 'SystemConstants.MEMORY_WARNING_THRESHOLD',
            r'\b80\b(?=\s*#.*CPU)': 'SystemConstants.CPU_WARNING_THRESHOLD',
            r'\b2\.0\b(?=\s*#.*API|\s*#.*api)': 'SystemConstants.SLOW_API_THRESHOLD',
            r'\b1\.0\b(?=\s*#.*查询|\s*#.*query)': 'SystemConstants.SLOW_QUERY_THRESHOLD',
            
            # 连接相关
            r'\b30\b(?=\s*#.*连接|\s*#.*connection)': 'SystemConstants.CONNECTION_TIMEOUT',
            r'\b60\b(?=\s*#.*查询|\s*#.*query)': 'SystemConstants.QUERY_TIMEOUT',
            r'\b20\b(?=\s*#.*连接|\s*#.*connection)': 'SystemConstants.MAX_CONNECTIONS',
            r'\b3\b(?=\s*#.*重试|\s*#.*retry)': 'SystemConstants.CONNECTION_RETRY_ATTEMPTS',
            
            # 端口相关
            r'\b1433\b(?=\s*#.*SQL|\s*#.*sql)': 'DefaultConfig.SQL_SERVER_PORT',
            r'\b3306\b(?=\s*#.*MySQL|\s*#.*mysql)': 'DefaultConfig.MYSQL_PORT',
            r'\b5432\b(?=\s*#.*PostgreSQL|\s*#.*postgres)': 'DefaultConfig.POSTGRES_PORT',
            r'\b1521\b(?=\s*#.*Oracle|\s*#.*oracle)': 'DefaultConfig.ORACLE_PORT',
            
            # 速率限制相关
            r'\b1000\b(?=\s*#.*请求|\s*#.*request)': 'SystemConstants.RATE_LIMIT_REQUESTS',
            r'\b5\b(?=\s*#.*登录|\s*#.*login)': 'SystemConstants.LOGIN_RATE_LIMIT',
        }
    
    def process_file(self, file_path: Path) -> bool:
        """处理单个文件"""
        try:
            if not file_path.suffix == '.py':
                return False
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            replacements_made = 0
            
            # 应用替换规则
            for pattern, replacement in self.replacements.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                    replacements_made += len(matches)
            
            # 如果有替换，写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✓ {file_path.relative_to(self.project_root)}: {replacements_made} 个替换")
                self.stats['replacements_made'] += replacements_made
                return True
            
            return False
            
        except Exception as e:
            print(f"✗ {file_path.relative_to(self.project_root)}: 错误 - {e}")
            self.stats['errors'] += 1
            return False
    
    def add_import_if_needed(self, file_path: Path) -> bool:
        """添加必要的导入语句"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否需要添加导入
            needs_import = False
            if 'SystemConstants.' in content and 'from app.constants import SystemConstants' not in content:
                needs_import = True
            if 'DefaultConfig.' in content and 'from app.constants import DefaultConfig' not in content:
                needs_import = True
            
            if needs_import:
                # 找到第一个import语句的位置
                import_match = re.search(r'^(import|from)\s+', content, re.MULTILINE)
                if import_match:
                    insert_pos = import_match.start()
                    import_line = "from app.constants import SystemConstants, DefaultConfig\n"
                    content = content[:insert_pos] + import_line + content[insert_pos:]
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"✓ {file_path.relative_to(self.project_root)}: 添加常量导入")
                    return True
            
            return False
            
        except Exception as e:
            print(f"✗ {file_path.relative_to(self.project_root)}: 导入错误 - {e}")
            return False
    
    def process_project(self) -> Dict[str, int]:
        """处理整个项目"""
        print("开始替换硬编码值...")
        
        # 处理所有Python文件
        for py_file in self.project_root.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            self.stats['files_processed'] += 1
            self.process_file(py_file)
            self.add_import_if_needed(py_file)
        
        print(f"\n替换完成!")
        print(f"处理文件: {self.stats['files_processed']}")
        print(f"替换次数: {self.stats['replacements_made']}")
        print(f"错误数量: {self.stats['errors']}")
        
        return self.stats

def main():
    """主函数"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    replacer = HardcodedValueReplacer(project_root)
    stats = replacer.process_project()
    
    if stats['replacements_made'] > 0:
        print("\n建议运行以下命令检查语法:")
        print("python -m py_compile app/*.py")
        print("python -m py_compile app/**/*.py")

if __name__ == '__main__':
    main()
