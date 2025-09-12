#!/usr/bin/env python3

"""
泰摸鱼吧 - 自动化部署脚本
提供一键部署、回滚、监控和健康检查功能
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from typing import Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class DeploymentManager:
    """部署管理器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.deployment_history = []
        self.current_version = None
        self.backup_dir = os.path.join(self.project_root, "deployments", "backups")
        self.logs_dir = os.path.join(self.project_root, "deployments", "logs")

        # 创建必要的目录
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        # 部署配置
        self.deployment_config = {
            "app_name": "taifish",
            "port": 5001,
            "workers": 4,
            "timeout": 30,
            "max_requests": 1000,
            "max_requests_jitter": 100,
            "preload_app": True,
            "bind": "0.0.0.0:5001",
            "accesslog": os.path.join(self.logs_dir, "access.log"),
            "errorlog": os.path.join(self.logs_dir, "error.log"),
            "loglevel": "info",
            "pidfile": os.path.join(self.project_root, "deployments", "gunicorn.pid"),
        }

    def deploy(self, environment: str = "production", backup: bool = True) -> dict[str, Any]:
        """执行部署"""
        logger.info(f"开始部署到 {environment} 环境...")

        deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()

        try:
            # 1. 预部署检查
            self._pre_deployment_checks()

            # 2. 备份当前版本
            if backup:
                self._backup_current_version(deployment_id)

            # 3. 更新代码
            self._update_code()

            # 4. 安装依赖
            self._install_dependencies()

            # 5. 运行数据库迁移
            self._run_database_migrations()

            # 6. 运行测试
            self._run_tests()

            # 7. 重启服务
            self._restart_services()

            # 8. 健康检查
            self._health_check()

            # 9. 记录部署信息
            deployment_info = {
                "deployment_id": deployment_id,
                "environment": environment,
                "timestamp": datetime.now().isoformat(),
                "duration": time.time() - start_time,
                "status": "success",
                "version": self._get_git_version(),
            }

            self.deployment_history.append(deployment_info)
            self._save_deployment_history()

            logger.info(f"部署成功: {deployment_id}")
            return deployment_info

        except Exception as e:
            logger.error(f"部署失败: {e}")

            # 回滚到上一个版本
            if backup and self.deployment_history:
                self._rollback()

            deployment_info = {
                "deployment_id": deployment_id,
                "environment": environment,
                "timestamp": datetime.now().isoformat(),
                "duration": time.time() - start_time,
                "status": "failed",
                "error": str(e),
            }

            self.deployment_history.append(deployment_info)
            self._save_deployment_history()

            return deployment_info

    def rollback(self, deployment_id: str = None) -> dict[str, Any]:
        """回滚到指定版本"""
        logger.info(f"开始回滚到版本: {deployment_id or 'latest'}")

        try:
            if deployment_id:
                # 回滚到指定版本
                self._rollback_to_version(deployment_id)
            else:
                # 回滚到上一个版本
                self._rollback()

            # 重启服务
            self._restart_services()

            # 健康检查
            self._health_check()

            logger.info("回滚成功")
            return {"status": "success", "message": "回滚成功"}

        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return {"status": "failed", "error": str(e)}

    def status(self) -> dict[str, Any]:
        """获取部署状态"""
        try:
            # 检查服务状态
            service_status = self._check_service_status()

            # 检查应用健康状态
            health_status = self._check_application_health()

            # 获取系统资源状态
            system_status = self._check_system_status()

            return {
                "service_status": service_status,
                "health_status": health_status,
                "system_status": system_status,
                "deployment_history": self.deployment_history[-5:],  # 最近5次部署
                "current_version": self._get_git_version(),
            }

        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return {"error": str(e)}

    def _pre_deployment_checks(self):
        """预部署检查"""
        logger.info("执行预部署检查...")

        # 检查Git状态
        if self._run_command("git status --porcelain"):
            raise Exception("工作目录有未提交的更改")

        # 检查Python版本
        python_version = sys.version_info
        if python_version < (3, 8):
            raise Exception(f"Python版本过低: {python_version}, 需要3.8+")

        # 检查磁盘空间
        disk_usage = shutil.disk_usage(self.project_root)
        free_space_gb = disk_usage.free / (1024**3)
        if free_space_gb < 1:
            raise Exception(f"磁盘空间不足: {free_space_gb:.2f}GB")

        # 检查端口是否被占用
        if self._is_port_in_use(self.deployment_config["port"]):
            logger.warning(f"端口 {self.deployment_config['port']} 已被占用")

        logger.info("预部署检查通过")

    def _backup_current_version(self, deployment_id: str):
        """备份当前版本"""
        logger.info("备份当前版本...")

        backup_path = os.path.join(self.backup_dir, deployment_id)
        os.makedirs(backup_path, exist_ok=True)

        # 备份代码
        shutil.copytree(
            self.project_root,
            os.path.join(backup_path, "code"),
            ignore=shutil.ignore_patterns("venv", "__pycache__", ".git", "*.pyc", "deployments"),
        )

        # 备份数据库
        self._backup_database(backup_path)

        # 备份配置文件
        config_files = [".env", "requirements.txt", "app.py"]
        for config_file in config_files:
            if os.path.exists(config_file):
                shutil.copy2(config_file, backup_path)

        logger.info(f"备份完成: {backup_path}")

    def _backup_database(self, backup_path: str):
        """备份数据库"""
        try:
            # 这里可以根据实际数据库类型进行备份
            # 示例：SQLite数据库备份
            db_file = os.path.join(self.project_root, "userdata", "taifish_dev.db")
            if os.path.exists(db_file):
                shutil.copy2(db_file, backup_path)
                logger.info("数据库备份完成")
        except Exception as e:
            logger.warning(f"数据库备份失败: {e}")

    def _update_code(self):
        """更新代码"""
        logger.info("更新代码...")

        # 拉取最新代码
        self._run_command("git pull origin main")

        # 更新子模块
        self._run_command("git submodule update --init --recursive")

        logger.info("代码更新完成")

    def _install_dependencies(self):
        """安装依赖"""
        logger.info("安装依赖...")

        # 激活虚拟环境并安装依赖
        venv_python = os.path.join(self.project_root, "venv", "bin", "python")
        if os.path.exists(venv_python):
            self._run_command(f"{venv_python} -m pip install --upgrade pip")
            self._run_command(f"{venv_python} -m pip install -r requirements.txt")
        else:
            raise Exception("虚拟环境不存在")

        logger.info("依赖安装完成")

    def _run_database_migrations(self):
        """运行数据库迁移"""
        logger.info("运行数据库迁移...")

        venv_python = os.path.join(self.project_root, "venv", "bin", "python")
        self._run_command(f"{venv_python} -m flask db upgrade")

        logger.info("数据库迁移完成")

    def _run_tests(self):
        """运行测试"""
        logger.info("运行测试...")

        venv_python = os.path.join(self.project_root, "venv", "bin", "python")

        # 运行单元测试
        result = self._run_command(f"{venv_python} -m pytest tests/ -v")
        if result.returncode != 0:
            raise Exception("单元测试失败")

        # 运行集成测试
        result = self._run_command(f"{venv_python} scripts/run_comprehensive_tests.py")
        if result.returncode != 0:
            raise Exception("集成测试失败")

        logger.info("测试通过")

    def _restart_services(self):
        """重启服务"""
        logger.info("重启服务...")

        # 停止现有服务
        self._stop_services()

        # 启动新服务
        self._start_services()

        logger.info("服务重启完成")

    def _stop_services(self):
        """停止服务"""
        # 停止Gunicorn进程
        pid_file = self.deployment_config["pidfile"]
        if os.path.exists(pid_file):
            with open(pid_file) as f:
                pid = int(f.read().strip())

            try:
                os.kill(pid, 15)  # SIGTERM
                time.sleep(5)

                # 如果进程还在运行，强制杀死
                try:
                    os.kill(pid, 9)  # SIGKILL
                except ProcessLookupError:
                    pass
            except ProcessLookupError:
                pass

            os.remove(pid_file)

    def _start_services(self):
        """启动服务"""
        venv_python = os.path.join(self.project_root, "venv", "bin", "python")
        gunicorn_cmd = os.path.join(self.project_root, "venv", "bin", "gunicorn")

        # 构建Gunicorn命令
        cmd = [
            gunicorn_cmd,
            "--bind",
            self.deployment_config["bind"],
            "--workers",
            str(self.deployment_config["workers"]),
            "--timeout",
            str(self.deployment_config["timeout"]),
            "--max-requests",
            str(self.deployment_config["max_requests"]),
            "--max-requests-jitter",
            str(self.deployment_config["max_requests_jitter"]),
            "--access-logfile",
            self.deployment_config["accesslog"],
            "--error-logfile",
            self.deployment_config["errorlog"],
            "--log-level",
            self.deployment_config["loglevel"],
            "--pid",
            self.deployment_config["pidfile"],
            "--daemon",
            "app:app",
        ]

        if self.deployment_config["preload_app"]:
            cmd.append("--preload")

        # 启动服务
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"启动服务失败: {result.stderr}")

        # 等待服务启动
        time.sleep(10)

    def _health_check(self):
        """健康检查"""
        logger.info("执行健康检查...")

        max_retries = 30
        retry_interval = 2

        for i in range(max_retries):
            try:
                import requests

                response = requests.get(f"http://localhost:{self.deployment_config['port']}/health/health", timeout=5)

                if response.status_code == 200:
                    logger.info("健康检查通过")
                    return

            except Exception as e:
                if i == max_retries - 1:
                    raise Exception(f"健康检查失败: {e}")

                logger.info(f"健康检查重试 {i + 1}/{max_retries}")
                time.sleep(retry_interval)

    def _check_service_status(self) -> dict[str, Any]:
        """检查服务状态"""
        pid_file = self.deployment_config["pidfile"]

        if not os.path.exists(pid_file):
            return {"status": "stopped", "pid": None}

        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())

            # 检查进程是否存在
            os.kill(pid, 0)
            return {"status": "running", "pid": pid}

        except (OSError, ValueError):
            return {"status": "stopped", "pid": None}

    def _check_application_health(self) -> dict[str, Any]:
        """检查应用健康状态"""
        try:
            import requests

            response = requests.get(f"http://localhost:{self.deployment_config['port']}/health/detailed", timeout=5)

            if response.status_code == 200:
                return response.json()
            return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _check_system_status(self) -> dict[str, Any]:
        """检查系统状态"""
        try:
            import psutil

            return {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
            }
        except Exception as e:
            return {"error": str(e)}

    def _rollback(self):
        """回滚到上一个版本"""
        if not self.deployment_history:
            raise Exception("没有可回滚的版本")

        # 获取上一个成功的部署
        successful_deployments = [d for d in self.deployment_history if d["status"] == "success"]
        if not successful_deployments:
            raise Exception("没有成功的部署版本")

        last_deployment = successful_deployments[-1]
        self._rollback_to_version(last_deployment["deployment_id"])

    def _rollback_to_version(self, deployment_id: str):
        """回滚到指定版本"""
        backup_path = os.path.join(self.backup_dir, deployment_id)

        if not os.path.exists(backup_path):
            raise Exception(f"备份版本不存在: {deployment_id}")

        logger.info(f"回滚到版本: {deployment_id}")

        # 停止服务
        self._stop_services()

        # 恢复代码
        code_backup = os.path.join(backup_path, "code")
        if os.path.exists(code_backup):
            # 备份当前代码
            current_backup = f"{self.project_root}_current_backup"
            if os.path.exists(current_backup):
                shutil.rmtree(current_backup)
            shutil.move(self.project_root, current_backup)

            # 恢复备份代码
            shutil.move(code_backup, self.project_root)

        # 恢复数据库
        db_backup = os.path.join(backup_path, "taifish_dev.db")
        if os.path.exists(db_backup):
            db_file = os.path.join(self.project_root, "userdata", "taifish_dev.db")
            shutil.copy2(db_backup, db_file)

        # 恢复配置文件
        for config_file in [".env", "requirements.txt", "app.py"]:
            config_backup = os.path.join(backup_path, config_file)
            if os.path.exists(config_backup):
                shutil.copy2(config_backup, self.project_root)

    def _get_git_version(self) -> str:
        """获取Git版本"""
        try:
            result = self._run_command("git rev-parse --short HEAD")
            return result.stdout.strip()
        except:
            return "unknown"

    def _is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) == 0

    def _run_command(self, command: str) -> subprocess.CompletedProcess:
        """运行命令"""
        logger.debug(f"执行命令: {command}")

        result = subprocess.run(command, shell=True, cwd=self.project_root, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"命令执行失败: {command}")
            logger.error(f"错误输出: {result.stderr}")

        return result

    def _save_deployment_history(self):
        """保存部署历史"""
        history_file = os.path.join(self.project_root, "deployments", "deployment_history.json")

        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(self.deployment_history, f, indent=2, ensure_ascii=False)

    def _load_deployment_history(self):
        """加载部署历史"""
        history_file = os.path.join(self.project_root, "deployments", "deployment_history.json")

        if os.path.exists(history_file):
            with open(history_file, encoding="utf-8") as f:
                self.deployment_history = json.load(f)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="泰摸鱼吧自动化部署工具")
    parser.add_argument("action", choices=["deploy", "rollback", "status"], help="操作类型")
    parser.add_argument("--environment", default="production", help="部署环境")
    parser.add_argument("--no-backup", action="store_true", help="跳过备份")
    parser.add_argument("--deployment-id", help="回滚到指定部署ID")

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("deployments/deployment.log"), logging.StreamHandler()],
    )

    # 创建部署管理器
    manager = DeploymentManager()
    manager._load_deployment_history()

    try:
        if args.action == "deploy":
            result = manager.deploy(args.environment, not args.no_backup)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.action == "rollback":
            result = manager.rollback(args.deployment_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.action == "status":
            result = manager.status()
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        logger.error(f"操作失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
