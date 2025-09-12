"""
定时任务管理路由
"""

import importlib.util
import logging
from datetime import datetime

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from flask import Blueprint, render_template, request
from flask_login import login_required

from app.scheduler import get_scheduler
from app.utils.api_response import APIResponse
from app.utils.decorators import scheduler_manage_required, scheduler_view_required

logger = logging.getLogger(__name__)

# 创建蓝图
scheduler_bp = Blueprint("scheduler", __name__, url_prefix="/scheduler")


@scheduler_bp.route("/")
@login_required
@scheduler_view_required
def index():
    """定时任务管理页面"""
    return render_template("scheduler/index.html")


@scheduler_bp.route("/api/jobs")
@login_required
@scheduler_view_required
def get_jobs():
    """获取所有定时任务"""
    try:
        scheduler = get_scheduler()
        if not scheduler.running:
            return APIResponse.error("调度器未启动", code=500)
        jobs = scheduler.get_jobs()
        logger.info(f"获取到 {len(jobs)} 个任务")
        jobs_data = []

        for job in jobs:
            # 检查任务状态
            is_paused = job.next_run_time is None
            is_builtin = job.id in ["sync_accounts", "cleanup_logs"]

            job_info = {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "func": job.func.__name__ if hasattr(job.func, "__name__") else str(job.func),
                "args": job.args,
                "kwargs": job.kwargs,
                "misfire_grace_time": job.misfire_grace_time,
                "max_instances": job.max_instances,
                "coalesce": job.coalesce,
                "is_paused": is_paused,
                "is_builtin": is_builtin,
                "status": "paused" if is_paused else "active",
            }
            jobs_data.append(job_info)

        return APIResponse.success(data=jobs_data, message="任务列表获取成功")

    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return APIResponse.error(f"获取任务列表失败: {str(e)}")


@scheduler_bp.route("/api/jobs/<job_id>")
@login_required
@scheduler_view_required
def get_job(job_id):
    """获取指定任务详情"""
    try:
        job = get_scheduler().get_job(job_id)
        if not job:
            return APIResponse.error("任务不存在", code=404)

        job_info = {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
            "func": job.func.__name__ if hasattr(job.func, "__name__") else str(job.func),
            "args": job.args,
            "kwargs": job.kwargs,
            "misfire_grace_time": job.misfire_grace_time,
            "max_instances": job.max_instances,
            "coalesce": job.coalesce,
        }

        return APIResponse.success(data=job_info, message="任务详情获取成功")

    except Exception as e:
        logger.error(f"获取任务详情失败: {e}")
        return APIResponse.error(f"获取任务详情失败: {str(e)}")


@scheduler_bp.route("/api/jobs", methods=["POST"])
@login_required
@scheduler_manage_required
def create_job():
    """创建新的定时任务"""
    try:
        data = request.get_json()
        logger.info(f"创建任务请求数据: {data}")

        # 验证必需字段
        required_fields = ["id", "name", "code", "trigger_type"]
        for field in required_fields:
            if field not in data:
                logger.error(f"缺少必需字段: {field}")
                return APIResponse.error(f"缺少必需字段: {field}", code=400)

        # 构建触发器
        trigger = _build_trigger(data)
        if not trigger:
            return APIResponse.error("无效的触发器配置", code=400)

        # 验证代码格式
        code = data["code"].strip()
        if not code:
            return APIResponse.error("任务代码不能为空", code=400)

        # 检查代码是否包含execute_task函数
        if "def execute_task():" not in code:
            return APIResponse.error("代码必须包含 'def execute_task():' 函数", code=400)

        # 创建动态任务函数
        task_func = _create_dynamic_task_function(data["id"], code)
        if not task_func:
            return APIResponse.error("代码格式错误，请检查语法", code=400)

        # 添加任务
        scheduler = get_scheduler()
        if not scheduler.running:
            return APIResponse.error("调度器未启动", code=500)

        # 直接使用函数对象
        job = scheduler.add_job(
            func=task_func, trigger=trigger, id=data["id"], name=data["name"], args=[], kwargs={}, replace_existing=True
        )

        logger.info(f"任务创建成功: {job.id}")
        return APIResponse.success(data={"job_id": job.id}, message="任务创建成功")

    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return APIResponse.error(f"创建任务失败: {str(e)}")


@scheduler_bp.route("/api/jobs/<job_id>", methods=["PUT"])
@login_required
@scheduler_manage_required
def update_job(job_id):
    """更新定时任务"""
    try:
        data = request.get_json()

        # 检查任务是否存在
        scheduler = get_scheduler()
        if not scheduler.running:
            return APIResponse.error("调度器未启动", code=500)

        job = scheduler.get_job(job_id)
        if not job:
            return APIResponse.error("任务不存在", code=404)

        # 检查是否为内置任务
        builtin_tasks = ["sync_accounts", "cleanup_logs"]
        is_builtin = job_id in builtin_tasks

        # 构建新的触发器
        if "trigger_type" in data:
            trigger = _build_trigger(data)
            if not trigger:
                return APIResponse.error("无效的触发器配置", code=400)

            if is_builtin:
                # 内置任务：只能更新触发器
                scheduler.modify_job(job_id, trigger=trigger)

                # 强制重新计算下次执行时间
                job = scheduler.get_job(job_id)
                if job:
                    # 重新调度任务以立即生效
                    scheduler.reschedule_job(job_id, trigger=trigger)

                logger.info(f"内置任务触发器更新成功: {job_id}")
                return APIResponse.success("触发器更新成功")
            # 自定义任务：可以更新所有属性
            scheduler.modify_job(
                job_id,
                trigger=trigger,
                name=data.get("name", job.name),
                args=data.get("args", job.args),
                kwargs=data.get("kwargs", job.kwargs),
            )

            # 强制重新计算下次执行时间
            job = scheduler.get_job(job_id)
            if job:
                # 重新调度任务以立即生效
                scheduler.reschedule_job(job_id, trigger=trigger)
        else:
            if is_builtin:
                # 内置任务：不允许更新其他属性
                return APIResponse.error("内置任务只能修改触发器", code=403)
            # 只更新其他属性
            scheduler.modify_job(
                job_id,
                name=data.get("name", job.name),
                args=data.get("args", job.args),
                kwargs=data.get("kwargs", job.kwargs),
            )

        logger.info(f"任务更新成功: {job_id}")
        return APIResponse.success("任务更新成功")

    except Exception as e:
        logger.error(f"更新任务失败: {e}")
        return APIResponse.error(f"更新任务失败: {str(e)}")


@scheduler_bp.route("/api/jobs/<job_id>", methods=["DELETE"])
@login_required
@scheduler_manage_required
def delete_job(job_id):
    """删除定时任务"""
    try:
        # 检查是否为内置任务
        builtin_tasks = ["sync_accounts", "cleanup_logs"]
        if job_id in builtin_tasks:
            return APIResponse.error("内置任务无法删除", code=403)

        scheduler = get_scheduler()
        if not scheduler.running:
            return APIResponse.error("调度器未启动", code=500)

        scheduler.remove_job(job_id)
        logger.info(f"任务删除成功: {job_id}")
        return APIResponse.success("任务删除成功")

    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return APIResponse.error(f"删除任务失败: {str(e)}")


@scheduler_bp.route("/api/jobs/<job_id>/disable", methods=["POST"])
@login_required
@scheduler_manage_required
def disable_job(job_id):
    """禁用定时任务"""
    try:
        scheduler = get_scheduler()
        if not scheduler.running:
            return APIResponse.error("调度器未启动", code=500)

        job = scheduler.get_job(job_id)
        if not job:
            return APIResponse.error("任务不存在", code=404)

        # 暂停任务
        scheduler.pause_job(job_id)
        logger.info(f"任务已禁用: {job_id}")
        return APIResponse.success(data={"job_id": job_id}, message="任务已禁用")

    except Exception as e:
        logger.error(f"禁用任务失败: {e}")
        return APIResponse.error(f"禁用任务失败: {str(e)}")


@scheduler_bp.route("/api/jobs/<job_id>/enable", methods=["POST"])
@login_required
@scheduler_manage_required
def enable_job(job_id):
    """启用定时任务"""
    try:
        scheduler = get_scheduler()
        if not scheduler.running:
            return APIResponse.error("调度器未启动", code=500)

        job = scheduler.get_job(job_id)
        if not job:
            return APIResponse.error("任务不存在", code=404)

        # 恢复任务
        scheduler.resume_job(job_id)
        logger.info(f"任务已启用: {job_id}")
        return APIResponse.success(data={"job_id": job_id}, message="任务已启用")

    except Exception as e:
        logger.error(f"启用任务失败: {e}")
        return APIResponse.error(f"启用任务失败: {str(e)}")


@scheduler_bp.route("/api/jobs/<job_id>/pause", methods=["POST"])
@login_required
@scheduler_manage_required
def pause_job(job_id):
    """暂停任务"""
    try:
        get_scheduler().pause_job(job_id)
        logger.info(f"任务暂停成功: {job_id}")
        return APIResponse.success("任务暂停成功")

    except Exception as e:
        logger.error(f"暂停任务失败: {e}")
        return APIResponse.error(f"暂停任务失败: {str(e)}")


@scheduler_bp.route("/api/jobs/<job_id>/resume", methods=["POST"])
@login_required
@scheduler_manage_required
def resume_job(job_id):
    """恢复任务"""
    try:
        get_scheduler().resume_job(job_id)
        logger.info(f"任务恢复成功: {job_id}")
        return APIResponse.success("任务恢复成功")

    except Exception as e:
        logger.error(f"恢复任务失败: {e}")
        return APIResponse.error(f"恢复任务失败: {str(e)}")


@scheduler_bp.route("/api/jobs/<job_id>/run", methods=["POST"])
@login_required
@scheduler_manage_required
def run_job(job_id):
    """立即执行任务"""
    try:
        scheduler = get_scheduler()
        if not scheduler.running:
            return APIResponse.error("调度器未启动", code=500)

        job = scheduler.get_job(job_id)
        if not job:
            return APIResponse.error("任务不存在", code=404)

        logger.info(f"开始立即执行任务: {job_id} - {job.name}")

        # 立即执行任务
        try:
            # 对于内置任务，直接调用任务函数（它们内部有应用上下文管理）
            if job_id in ["sync_accounts", "cleanup_logs"]:
                result = job.func(*job.args, **job.kwargs)
                logger.info(f"任务立即执行成功: {job_id} - 结果: {result}")
                return APIResponse.success(data={"result": str(result)}, message="任务执行成功")
            # 对于自定义任务，需要手动管理应用上下文
            from app import create_app

            app = create_app()
            with app.app_context():
                result = job.func(*job.args, **job.kwargs)
                logger.info(f"任务立即执行成功: {job_id} - 结果: {result}")
                return APIResponse.success(data={"result": str(result)}, message="任务执行成功")
        except Exception as func_error:
            logger.error(f"任务函数执行失败: {job_id} - {func_error}")
            return APIResponse.error(f"任务执行失败: {str(func_error)}")

    except Exception as e:
        logger.error(f"执行任务失败: {e}")
        return APIResponse.error(f"执行任务失败: {str(e)}")


def _get_task_function(func_name):
    """获取任务函数"""
    from app.tasks import backup_database, cleanup_old_logs, generate_reports, sync_accounts

    # 任务函数映射
    task_functions = {
        "cleanup_old_logs": cleanup_old_logs,
        "backup_database": backup_database,
        "sync_accounts": sync_accounts,
        "generate_reports": generate_reports,
    }

    return task_functions.get(func_name)


def _create_dynamic_task_function(job_id, code):
    """创建动态任务函数"""
    try:
        import os
        import sys

        # 创建动态任务目录
        dynamic_tasks_dir = "userdata/dynamic_tasks"
        os.makedirs(dynamic_tasks_dir, exist_ok=True)

        # 生成任务文件路径
        task_file = os.path.join(dynamic_tasks_dir, f"{job_id}.py")

        # 创建完整的任务代码
        full_code = f'''"""
动态任务: {job_id}
创建时间: {datetime.now().isoformat()}
"""

from app import create_app, db
import logging

logger = logging.getLogger(__name__)

{code}

def task_wrapper():
    """任务包装器"""
    try:
        logger.info(f"开始执行动态任务: {job_id}")
        result = execute_task()
        logger.info(f"动态任务 {job_id} 执行完成: {{result}}")
        return result
    except Exception as e:
        logger.error(f"动态任务 {job_id} 执行失败: {{e}}")
        return f"任务执行失败: {{e}}"
'''

        # 保存任务文件
        with open(task_file, "w", encoding="utf-8") as f:
            f.write(full_code)

        # 将动态任务目录添加到Python路径
        if dynamic_tasks_dir not in sys.path:
            sys.path.insert(0, dynamic_tasks_dir)

        # 动态导入模块
        module_name = job_id
        spec = importlib.util.spec_from_file_location(module_name, task_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # 返回模块中的task_wrapper函数
        return module.task_wrapper

    except Exception as e:
        logger.error(f"创建动态任务函数失败: {e}")
        return None


def _build_trigger(data):
    """构建触发器"""
    trigger_type = data.get("trigger_type")

    if trigger_type == "cron":
        return CronTrigger(
            year=data.get("year"),
            month=data.get("month"),
            day=data.get("day"),
            week=data.get("week"),
            day_of_week=data.get("day_of_week"),
            hour=data.get("hour"),
            minute=data.get("minute"),
            second=data.get("second"),
        )
    if trigger_type == "interval":
        # 过滤掉None值
        kwargs = {}
        for key in ["weeks", "days", "hours", "minutes", "seconds"]:
            value = data.get(key)
            if value is not None and value > 0:
                kwargs[key] = value

        if not kwargs:
            return None

        return IntervalTrigger(**kwargs)
    if trigger_type == "date":
        run_date = data.get("run_date")
        if run_date:
            from datetime import datetime

            return DateTrigger(run_date=datetime.fromisoformat(run_date))

    return None
