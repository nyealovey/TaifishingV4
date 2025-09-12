"""
泰摸鱼吧 - 代码质量分析工具
提供代码质量检查、复杂度分析、重复代码检测和重构建议
"""

import ast
import logging
import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CodeIssue:
    """代码问题数据类"""

    file_path: str
    line_number: int
    issue_type: str
    severity: str
    message: str
    suggestion: str
    code_snippet: str = ""


@dataclass
class CodeMetrics:
    """代码指标数据类"""

    file_path: str
    lines_of_code: int
    cyclomatic_complexity: int
    function_count: int
    class_count: int
    import_count: int
    comment_ratio: float
    duplicate_lines: int
    maintainability_index: float


class CodeQualityAnalyzer:
    """代码质量分析器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.issues = []
        self.metrics = {}
        self.duplicate_patterns = {}

        # 代码质量规则
        self.rules = {
            "function_length": {"max_lines": 50, "severity": "warning"},
            "class_length": {"max_lines": 200, "severity": "warning"},
            "cyclomatic_complexity": {"max_complexity": 10, "severity": "warning"},
            "parameter_count": {"max_params": 5, "severity": "warning"},
            "nested_depth": {"max_depth": 4, "severity": "warning"},
            "line_length": {"max_length": 120, "severity": "info"},
            "magic_numbers": {"severity": "warning"},
            "unused_imports": {"severity": "info"},
            "unused_variables": {"severity": "warning"},
            "duplicate_code": {"min_lines": 5, "severity": "warning"},
            "missing_docstrings": {"severity": "info"},
            "naming_conventions": {"severity": "warning"},
        }

    def analyze_project(self) -> dict[str, Any]:
        """分析整个项目"""
        logger.info("开始分析项目代码质量...")

        python_files = self._find_python_files()

        for file_path in python_files:
            try:
                self._analyze_file(file_path)
            except Exception as e:
                logger.error(f"分析文件失败: {file_path}, 错误: {e}")

        # 检测重复代码
        self._detect_duplicate_code()

        # 生成报告
        return self._generate_quality_report()

    def _find_python_files(self) -> list[str]:
        """查找Python文件"""
        python_files = []

        for root, dirs, files in os.walk(self.project_root):
            # 跳过虚拟环境和缓存目录
            dirs[:] = [d for d in dirs if d not in ["venv", "__pycache__", ".git", "node_modules"]]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        return python_files

    def _analyze_file(self, file_path: str):
        """分析单个文件"""
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # 解析AST
            tree = ast.parse(content, filename=file_path)

            # 计算代码指标
            metrics = self._calculate_metrics(file_path, content, tree)
            self.metrics[file_path] = metrics

            # 检查代码问题
            self._check_code_issues(file_path, content, tree)

        except SyntaxError as e:
            self.issues.append(
                CodeIssue(
                    file_path=file_path,
                    line_number=e.lineno or 0,
                    issue_type="syntax_error",
                    severity="error",
                    message=f"语法错误: {e.msg}",
                    suggestion="修复语法错误",
                )
            )
        except Exception as e:
            logger.error(f"分析文件时出错: {file_path}, 错误: {e}")

    def _calculate_metrics(self, file_path: str, content: str, tree: ast.AST) -> CodeMetrics:
        """计算代码指标"""
        lines = content.split("\n")

        # 基本指标
        lines_of_code = len([line for line in lines if line.strip() and not line.strip().startswith("#")])
        comment_lines = len([line for line in lines if line.strip().startswith("#")])
        comment_ratio = comment_lines / len(lines) if lines else 0

        # 函数和类统计
        function_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
        class_count = len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
        import_count = len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))])

        # 圈复杂度
        cyclomatic_complexity = self._calculate_cyclomatic_complexity(tree)

        # 可维护性指数
        maintainability_index = self._calculate_maintainability_index(
            lines_of_code, cyclomatic_complexity, comment_ratio
        )

        return CodeMetrics(
            file_path=file_path,
            lines_of_code=lines_of_code,
            cyclomatic_complexity=cyclomatic_complexity,
            function_count=function_count,
            class_count=class_count,
            import_count=import_count,
            comment_ratio=comment_ratio,
            duplicate_lines=0,  # 将在重复代码检测中计算
            maintainability_index=maintainability_index,
        )

    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1  # 基础复杂度

        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor))
                or isinstance(node, ast.ExceptHandler)
                or isinstance(node, (ast.And, ast.Or))
            ):
                complexity += 1

        return complexity

    def _calculate_maintainability_index(
        self, lines_of_code: int, cyclomatic_complexity: int, comment_ratio: float
    ) -> float:
        """计算可维护性指数 (0-100)"""
        # 基于Halstead复杂度、圈复杂度和代码行数
        if lines_of_code == 0:
            return 100.0

        # 简化的可维护性指数计算
        volume = lines_of_code * (1 + cyclomatic_complexity)
        maintainability = max(0, 100 - (volume / 100) - (cyclomatic_complexity * 2) + (comment_ratio * 20))

        return min(100, max(0, maintainability))

    def _check_code_issues(self, file_path: str, content: str, tree: ast.AST):
        """检查代码问题"""
        lines = content.split("\n")

        # 检查函数长度
        self._check_function_length(file_path, tree, lines)

        # 检查类长度
        self._check_class_length(file_path, tree, lines)

        # 检查圈复杂度
        self._check_cyclomatic_complexity(file_path, tree)

        # 检查参数数量
        self._check_parameter_count(file_path, tree)

        # 检查嵌套深度
        self._check_nested_depth(file_path, tree)

        # 检查行长度
        self._check_line_length(file_path, lines)

        # 检查魔法数字
        self._check_magic_numbers(file_path, tree)

        # 检查未使用的导入
        self._check_unused_imports(file_path, tree)

        # 检查未使用的变量
        self._check_unused_variables(file_path, tree)

        # 检查文档字符串
        self._check_docstrings(file_path, tree)

        # 检查命名约定
        self._check_naming_conventions(file_path, tree)

    def _check_function_length(self, file_path: str, tree: ast.AST, lines: list[str]):
        """检查函数长度"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start_line = node.lineno
                end_line = node.end_lineno or start_line
                function_lines = end_line - start_line + 1

                if function_lines > self.rules["function_length"]["max_lines"]:
                    self.issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=start_line,
                            issue_type="function_length",
                            severity=self.rules["function_length"]["severity"],
                            message=f"函数 '{node.name}' 过长 ({function_lines} 行)",
                            suggestion=f"将函数拆分为更小的函数，建议不超过 {self.rules['function_length']['max_lines']} 行",
                            code_snippet=lines[start_line - 1 : end_line],
                        )
                    )

    def _check_class_length(self, file_path: str, tree: ast.AST, lines: list[str]):
        """检查类长度"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                start_line = node.lineno
                end_line = node.end_lineno or start_line
                class_lines = end_line - start_line + 1

                if class_lines > self.rules["class_length"]["max_lines"]:
                    self.issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=start_line,
                            issue_type="class_length",
                            severity=self.rules["class_length"]["severity"],
                            message=f"类 '{node.name}' 过长 ({class_lines} 行)",
                            suggestion=f"将类拆分为更小的类，建议不超过 {self.rules['class_length']['max_lines']} 行",
                            code_snippet=lines[start_line - 1 : end_line],
                        )
                    )

    def _check_cyclomatic_complexity(self, file_path: str, tree: ast.AST):
        """检查圈复杂度"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_cyclomatic_complexity(node)

                if complexity > self.rules["cyclomatic_complexity"]["max_complexity"]:
                    self.issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="cyclomatic_complexity",
                            severity=self.rules["cyclomatic_complexity"]["severity"],
                            message=f"函数 '{node.name}' 圈复杂度过高 ({complexity})",
                            suggestion=f"简化函数逻辑，建议复杂度不超过 {self.rules['cyclomatic_complexity']['max_complexity']}",
                            code_snippet=f"def {node.name}(...):",
                        )
                    )

    def _check_parameter_count(self, file_path: str, tree: ast.AST):
        """检查参数数量"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                param_count = len(node.args.args)

                if param_count > self.rules["parameter_count"]["max_params"]:
                    self.issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="parameter_count",
                            severity=self.rules["parameter_count"]["severity"],
                            message=f"函数 '{node.name}' 参数过多 ({param_count} 个)",
                            suggestion=f"减少参数数量，建议不超过 {self.rules['parameter_count']['max_params']} 个",
                            code_snippet=f"def {node.name}(...):",
                        )
                    )

    def _check_nested_depth(self, file_path: str, tree: ast.AST):
        """检查嵌套深度"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                max_depth = self._calculate_nested_depth(node)

                if max_depth > self.rules["nested_depth"]["max_depth"]:
                    self.issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="nested_depth",
                            severity=self.rules["nested_depth"]["severity"],
                            message=f"函数 '{node.name}' 嵌套过深 ({max_depth} 层)",
                            suggestion=f"减少嵌套层级，建议不超过 {self.rules['nested_depth']['max_depth']} 层",
                            code_snippet=f"def {node.name}(...):",
                        )
                    )

    def _calculate_nested_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """计算嵌套深度"""
        max_depth = current_depth

        for child in ast.iter_child_nodes(node):
            if isinstance(
                child,
                (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.AsyncWith),
            ):
                depth = self._calculate_nested_depth(child, current_depth + 1)
                max_depth = max(max_depth, depth)
            else:
                depth = self._calculate_nested_depth(child, current_depth)
                max_depth = max(max_depth, depth)

        return max_depth

    def _check_line_length(self, file_path: str, lines: list[str]):
        """检查行长度"""
        for i, line in enumerate(lines, 1):
            if len(line) > self.rules["line_length"]["max_length"]:
                self.issues.append(
                    CodeIssue(
                        file_path=file_path,
                        line_number=i,
                        issue_type="line_length",
                        severity=self.rules["line_length"]["severity"],
                        message=f"行过长 ({len(line)} 字符)",
                        suggestion=f"将长行拆分为多行，建议不超过 {self.rules['line_length']['max_length']} 字符",
                        code_snippet=line,
                    )
                )

    def _check_magic_numbers(self, file_path: str, tree: ast.AST):
        """检查魔法数字"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                # 跳过常见的非魔法数字
                if node.value in [0, 1, -1, 2, 10, 100, 1000]:
                    continue

                # 检查是否在函数调用或比较中
                parent = getattr(node, "parent", None)
                if parent and isinstance(parent, (ast.Call, ast.Compare)):
                    self.issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="magic_number",
                            severity=self.rules["magic_numbers"]["severity"],
                            message=f"发现魔法数字: {node.value}",
                            suggestion="将魔法数字定义为常量",
                            code_snippet=str(node.value),
                        )
                    )

    def _check_unused_imports(self, file_path: str, tree: ast.AST):
        """检查未使用的导入"""
        imports = []
        used_names = set()

        # 收集所有导入
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append((node.lineno, alias.name, alias.asname or alias.name))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    full_name = f"{node.module}.{alias.name}" if node.module else alias.name
                    imports.append((node.lineno, full_name, alias.asname or alias.name))

        # 收集所有使用的名称
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                used_names.add(node.attr)

        # 检查未使用的导入
        for line_no, full_name, local_name in imports:
            if local_name not in used_names:
                self.issues.append(
                    CodeIssue(
                        file_path=file_path,
                        line_number=line_no,
                        issue_type="unused_import",
                        severity=self.rules["unused_imports"]["severity"],
                        message=f"未使用的导入: {full_name}",
                        suggestion="删除未使用的导入",
                        code_snippet=f"import {full_name}",
                    )
                )

    def _check_unused_variables(self, file_path: str, tree: ast.AST):
        """检查未使用的变量"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 获取函数参数
                {arg.arg for arg in node.args.args}

                # 获取函数中使用的变量
                used_vars = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                        used_vars.add(child.id)

                # 检查未使用的参数
                for arg in node.args.args:
                    if arg.arg not in used_vars and not arg.arg.startswith("_"):
                        self.issues.append(
                            CodeIssue(
                                file_path=file_path,
                                line_number=node.lineno,
                                issue_type="unused_variable",
                                severity=self.rules["unused_variables"]["severity"],
                                message=f"未使用的参数: {arg.arg}",
                                suggestion="删除未使用的参数或使用下划线前缀",
                                code_snippet=f"def {node.name}({arg.arg}, ...):",
                            )
                        )

    def _check_docstrings(self, file_path: str, tree: ast.AST):
        """检查文档字符串"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    self.issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="missing_docstring",
                            severity=self.rules["missing_docstrings"]["severity"],
                            message=f"{'类' if isinstance(node, ast.ClassDef) else '函数'} '{node.name}' 缺少文档字符串",
                            suggestion="添加文档字符串描述功能",
                            code_snippet=f"{'class' if isinstance(node, ast.ClassDef) else 'def'} {node.name}(...):",
                        )
                    )

    def _check_naming_conventions(self, file_path: str, tree: ast.AST):
        """检查命名约定"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r"^[a-z_][a-z0-9_]*$", node.name):
                    self.issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="naming_convention",
                            severity=self.rules["naming_conventions"]["severity"],
                            message=f"函数名不符合约定: {node.name}",
                            suggestion="使用小写字母和下划线命名函数",
                            code_snippet=f"def {node.name}(...):",
                        )
                    )
            elif isinstance(node, ast.ClassDef):
                if not re.match(r"^[A-Z][a-zA-Z0-9]*$", node.name):
                    self.issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            issue_type="naming_convention",
                            severity=self.rules["naming_conventions"]["severity"],
                            message=f"类名不符合约定: {node.name}",
                            suggestion="使用大驼峰命名类",
                            code_snippet=f"class {node.name}(...):",
                        )
                    )

    def _detect_duplicate_code(self):
        """检测重复代码"""
        # 简化的重复代码检测
        file_contents = {}

        for file_path in self.metrics.keys():
            try:
                with open(file_path, encoding="utf-8") as f:
                    file_contents[file_path] = f.read().split("\n")
            except Exception as e:
                logger.error(f"读取文件失败: {file_path}, 错误: {e}")

        # 检测重复的代码块
        for file1, lines1 in file_contents.items():
            for file2, lines2 in file_contents.items():
                if file1 >= file2:  # 避免重复比较
                    continue

                # 查找相同的代码行序列
                for i in range(len(lines1) - 4):  # 至少5行
                    for j in range(len(lines2) - 4):
                        if lines1[i : i + 5] == lines2[j : j + 5]:
                            # 找到重复代码
                            self.issues.append(
                                CodeIssue(
                                    file_path=file1,
                                    line_number=i + 1,
                                    issue_type="duplicate_code",
                                    severity=self.rules["duplicate_code"]["severity"],
                                    message=f"重复代码 (与 {file2}:{j + 1} 相同)",
                                    suggestion="提取重复代码为公共函数",
                                    code_snippet="\n".join(lines1[i : i + 5]),
                                )
                            )

    def _generate_quality_report(self) -> dict[str, Any]:
        """生成质量报告"""
        # 统计问题
        issue_stats = Counter(issue.issue_type for issue in self.issues)
        severity_stats = Counter(issue.severity for issue in self.issues)

        # 计算总体指标
        total_files = len(self.metrics)
        total_lines = sum(metrics.lines_of_code for metrics in self.metrics.values())
        avg_complexity = (
            sum(metrics.cyclomatic_complexity for metrics in self.metrics.values()) / total_files
            if total_files > 0
            else 0
        )
        avg_maintainability = (
            sum(metrics.maintainability_index for metrics in self.metrics.values()) / total_files
            if total_files > 0
            else 0
        )

        # 生成建议
        suggestions = self._generate_suggestions()

        return {
            "summary": {
                "total_files": total_files,
                "total_lines": total_lines,
                "total_issues": len(self.issues),
                "avg_complexity": round(avg_complexity, 2),
                "avg_maintainability": round(avg_maintainability, 2),
                "issue_types": dict(issue_stats),
                "severity_distribution": dict(severity_stats),
            },
            "issues": [
                {
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "code_snippet": issue.code_snippet,
                }
                for issue in self.issues
            ],
            "metrics": {
                file_path: {
                    "lines_of_code": metrics.lines_of_code,
                    "cyclomatic_complexity": metrics.cyclomatic_complexity,
                    "function_count": metrics.function_count,
                    "class_count": metrics.class_count,
                    "comment_ratio": round(metrics.comment_ratio, 2),
                    "maintainability_index": round(metrics.maintainability_index, 2),
                }
                for file_path, metrics in self.metrics.items()
            },
            "suggestions": suggestions,
        }

    def _generate_suggestions(self) -> list[dict[str, Any]]:
        """生成改进建议"""
        suggestions = []

        # 基于问题统计生成建议
        issue_types = Counter(issue.issue_type for issue in self.issues)

        if issue_types.get("function_length", 0) > 0:
            suggestions.append(
                {
                    "category": "code_structure",
                    "priority": "medium",
                    "title": "函数过长问题",
                    "description": f"发现 {issue_types['function_length']} 个函数过长",
                    "actions": [
                        "将长函数拆分为更小的函数",
                        "提取公共逻辑为独立函数",
                        "使用组合模式重构复杂逻辑",
                    ],
                }
            )

        if issue_types.get("cyclomatic_complexity", 0) > 0:
            suggestions.append(
                {
                    "category": "complexity",
                    "priority": "high",
                    "title": "圈复杂度过高",
                    "description": f"发现 {issue_types['cyclomatic_complexity']} 个函数复杂度过高",
                    "actions": [
                        "简化条件逻辑",
                        "使用策略模式替换复杂的if-else",
                        "提取方法减少嵌套",
                    ],
                }
            )

        if issue_types.get("duplicate_code", 0) > 0:
            suggestions.append(
                {
                    "category": "code_duplication",
                    "priority": "medium",
                    "title": "重复代码",
                    "description": f"发现 {issue_types['duplicate_code']} 处重复代码",
                    "actions": [
                        "提取重复代码为公共函数",
                        "使用继承或组合减少重复",
                        "创建工具类封装公共逻辑",
                    ],
                }
            )

        if issue_types.get("missing_docstring", 0) > 0:
            suggestions.append(
                {
                    "category": "documentation",
                    "priority": "low",
                    "title": "缺少文档字符串",
                    "description": f"发现 {issue_types['missing_docstring']} 个函数/类缺少文档",
                    "actions": [
                        "为所有公共函数添加文档字符串",
                        "使用JSDoc风格编写文档",
                        "添加参数和返回值说明",
                    ],
                }
            )

        return suggestions


# 全局代码质量分析器实例
code_quality_analyzer = CodeQualityAnalyzer()
