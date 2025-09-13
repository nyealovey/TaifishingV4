"""
泰摸鱼吧 - 错误日志中间件
确保所有未捕获的异常都被正确记录到系统日志
"""

import traceback
import uuid
from datetime import datetime

from flask import Flask, Response, g, request
from flask_login import current_user

from app import db
from app.models.log import Log
from app.utils.enhanced_logger import enhanced_logger, log_exception


def determine_log_source() -> str:
    """确定日志来源"""
    try:
        # 检查是否有用户认证
        if current_user and hasattr(current_user, "id") and current_user.is_authenticated:
            # 有用户认证的请求
            if request.path.startswith("/api/"):
                return "api_call"  # API调用
            return "web_request"  # 网页请求
        # 无用户认证的请求
        if request.path.startswith("/api/"):
            return "api_call"  # API调用
        return "system_operation"  # 系统操作
    except Exception:
        return "system_operation"  # 默认系统操作


def register_error_logging_middleware(app: Flask) -> None:
    """注册错误日志中间件"""
    print("DEBUG: 注册错误日志中间件")

    @app.before_request
    def log_request_start() -> None:
        """记录请求开始"""
        print(f"DEBUG: before_request 被调用: {request.method} {request.path}")
        try:
            if request.endpoint and not request.endpoint.startswith("static"):
                # 为每个请求生成唯一ID
                request_id = str(uuid.uuid4())[:8]  # 使用UUID的前8位
                g.request_id = request_id

                # 确定日志来源
                log_source = determine_log_source()

                enhanced_logger.info(
                    f"请求开始: {request.method} {request.path} [request_id: {request_id}]",
                    "request_handler",
                    f"用户: {current_user.id if current_user and hasattr(current_user, 'id') else 'anonymous'}, "
                    f"IP: {request.remote_addr}, "
                    f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}",
                    source=log_source,
                )
        except Exception:
            # 避免在日志记录过程中出错
            pass

    @app.after_request
    def log_request_end(response: Response) -> None:
        """记录请求结束并合并日志"""
        print(f"DEBUG: after_request 被调用: {request.method} {request.path} - {response.status_code}")
        print(f"DEBUG: request.endpoint: {request.endpoint}")

        try:
            # 只处理HTTP请求，不处理静态文件和其他类型的日志
            if (
                request.endpoint
                and not request.endpoint.startswith("static")
                and request.method in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
            ):
                print("DEBUG: 处理HTTP请求")
                status_code = response.status_code
                request_id = getattr(g, "request_id", "unknown")
                print(
                    f"DEBUG: 处理请求结束: {request.method} {request.path} - {status_code} [request_id: {request_id}]"
                )

                # 查找对应的开始日志
                start_log = None
                if request_id != "unknown":
                    search_pattern = f"%请求开始: {request.method} {request.path} [request_id: {request_id}]%"
                    print(f"DEBUG: 查找开始日志，模式: {search_pattern}")
                    start_log = (
                        Log.query.filter(Log.message.like(search_pattern)).order_by(Log.created_at.desc()).first()
                    )
                    print(f"DEBUG: 找到开始日志: {start_log.id if start_log else 'None'}")

                if start_log:
                    print("DEBUG: 开始合并日志")
                    # 计算持续时间
                    from datetime import datetime

                    end_time = datetime.utcnow()
                    duration = (end_time - start_log.created_at).total_seconds() * 1000

                    # 检查是否是批量同步操作
                    is_batch_sync = request.path == "/account-sync/sync-all" and request.method == "POST"

                    if is_batch_sync:
                        print("DEBUG: 检测到批量同步操作，进行特殊合并处理")
                        # 查找所有相关的同步日志
                        sync_logs = _find_related_sync_logs(start_log.created_at, end_time)
                        print(f"DEBUG: 找到 {len(sync_logs)} 条相关同步日志")

                        # 合并所有相关日志
                        merged_log = _merge_batch_sync_logs(
                            start_log, sync_logs, end_time, duration, status_code, response
                        )

                        if merged_log:
                            # 删除所有相关的原始日志
                            for log in sync_logs:
                                db.session.delete(log)
                            db.session.delete(start_log)

                            # 提交事务
                            db.session.commit()
                            print(f"DEBUG: 批量同步日志合并完成，新日志ID: {merged_log.id}")
                    else:
                        # 普通请求的合并逻辑
                        merged_log = _merge_regular_request_logs(start_log, end_time, duration, status_code, response)

                        if merged_log:
                            # 删除原始的开始日志
                            db.session.delete(start_log)

                            # 提交事务
                            db.session.commit()
                            print(f"DEBUG: 合并日志完成，新日志ID: {merged_log.id}")
                else:
                    print("DEBUG: 没有找到开始日志，记录结束日志")
                    # 如果没有找到开始日志，记录结束日志
                    log_level = "warning" if status_code >= 400 else "info"
                    getattr(enhanced_logger, log_level)(
                        f"请求结束: {request.method} {request.path} - {status_code} [request_id: {request_id}]",
                        "request_handler",
                        f"用户: {current_user.id if current_user and hasattr(current_user, 'id') else 'anonymous'}, "
                        f"IP: {request.remote_addr}, "
                        f"响应大小: {response.content_length or 0} bytes",
                    )
        except Exception as e:
            # 记录中间件错误
            print(f"ERROR: 中间件错误: {e}")
            import traceback

            traceback.print_exc()

        return response

    @app.errorhandler(400)
    def handle_bad_request(error: Exception) -> None:
        """处理400错误"""
        log_exception(error, "客户端请求错误", "error_handler", "WARNING")
        return {"error": "请求参数错误", "message": str(error), "status_code": 400}, 400

    @app.errorhandler(401)
    def handle_unauthorized(error: Exception) -> None:
        """处理401错误"""
        log_exception(error, "未授权访问", "error_handler", "WARNING")
        return {"error": "未授权访问", "message": "请先登录", "status_code": 401}, 401

    @app.errorhandler(403)
    def handle_forbidden(error: Exception) -> None:
        """处理403错误"""
        log_exception(error, "禁止访问", "error_handler", "WARNING")
        return {"error": "禁止访问", "message": "您没有权限访问此资源", "status_code": 403}, 403

    @app.errorhandler(404)
    def handle_not_found(error: Exception) -> None:
        """处理404错误"""
        from flask import request

        url = request.url if request else "未知URL"
        method = request.method if request else "未知方法"
        log_exception(error, f"资源未找到 - {method} {url}", "error_handler", "WARNING")
        return {"error": "资源未找到", "message": "请求的资源不存在", "status_code": 404}, 404

    @app.errorhandler(500)
    def handle_internal_server_error(error: Exception) -> None:
        """处理500错误"""
        log_exception(error, "服务器内部错误", "error_handler", "ERROR")
        return {"error": "服务器内部错误", "message": "系统出现错误，请稍后重试", "status_code": 500}, 500

    @app.errorhandler(Exception)
    def handle_unhandled_exception(error: Exception) -> None:
        """处理所有未捕获的异常"""
        # 记录详细的错误信息
        log_exception(error, "未处理的异常", "error_handler", "ERROR")

        # 记录到数据库
        try:
            Log.log_error(
                message=f"未处理的异常: {type(error).__name__}: {str(error)}",
                module="error_handler",
                details=f"请求: {request.method} {request.path}\n"
                f"用户: {current_user.id if current_user and hasattr(current_user, 'id') else 'anonymous'}\n"
                f"IP: {request.remote_addr}\n"
                f"堆栈跟踪:\n{traceback.format_exc()}",
                user_id=current_user.id if current_user and hasattr(current_user, "id") else None,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )
        except Exception as log_error:
            # 如果数据库记录也失败，至少记录到文件
            enhanced_logger.critical(f"记录错误日志失败: {log_error}", "error_handler")

        return {"error": "系统错误", "message": "系统出现错误，请稍后重试", "status_code": 500}, 500


def log_database_operation_error(operation: str, error: Exception, module: str | None = None, details: str | None = None) -> None:
    """记录数据库操作错误"""
    try:
        Log.log_error(
            message=f"数据库操作失败: {operation}",
            module=module or "database",
            details=f"{details or ''}\n错误类型: {type(error).__name__}\n错误信息: {str(error)}\n堆栈跟踪:\n{traceback.format_exc()}",
            user_id=current_user.id if current_user and hasattr(current_user, "id") else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get("User-Agent") if request else None,
        )
    except Exception as log_error:
        enhanced_logger.critical(f"记录数据库错误日志失败: {log_error}", "database")


def log_api_operation_error(endpoint: str, error: Exception, module: str | None = None, details: str | None = None) -> None:
    """记录API操作错误"""
    try:
        Log.log_error(
            message=f"API操作失败: {endpoint}",
            module=module or "api",
            details=f"{details or ''}\n错误类型: {type(error).__name__}\n错误信息: {str(error)}\n堆栈跟踪:\n{traceback.format_exc()}",
            user_id=current_user.id if current_user and hasattr(current_user, "id") else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get("User-Agent") if request else None,
        )
    except Exception as log_error:
        enhanced_logger.critical(f"记录API错误日志失败: {log_error}", "api")


def log_sync_operation_error(operation: str, error: Exception, module: str | None = None, details: str | None = None) -> None:
    """记录同步操作错误"""
    try:
        Log.log_error(
            message=f"同步操作失败: {operation}",
            module=module or "sync",
            details=f"{details or ''}\n错误类型: {type(error).__name__}\n错误信息: {str(error)}\n堆栈跟踪:\n{traceback.format_exc()}",
            user_id=current_user.id if current_user and hasattr(current_user, "id") else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get("User-Agent") if request else None,
        )
    except Exception as log_error:
        enhanced_logger.critical(f"记录同步错误日志失败: {log_error}", "sync")


def _find_related_sync_logs(start_time: datetime, end_time: datetime) -> list:
    """查找与批量同步相关的所有日志"""
    try:
        # 查找在时间范围内的所有同步相关日志
        sync_logs = (
            Log.query.filter(
                Log.created_at >= start_time,
                Log.created_at <= end_time,
                Log.module.in_(["account_sync_service", "enhanced_logger"]),
                Log.message.like("%同步%"),
            )
            .order_by(Log.created_at.asc())
            .all()
        )

        return sync_logs
    except Exception as e:
        print(f"DEBUG: 查找相关同步日志失败: {e}")
        return []


def _merge_batch_sync_logs(start_log: Log, sync_logs: list, end_time: datetime, duration: float, status_code: int, response: Response) -> None:
    """合并批量同步日志"""
    try:
        # 统计信息
        total_instances = 0
        success_count = 0
        failed_count = 0
        total_accounts = 0

        # 解析同步日志
        for log in sync_logs:
            if "开始账户同步:" in log.message:
                total_instances += 1
            elif "成功同步" in log.message and "个" in log.message:
                success_count += 1
                # 提取同步的账户数量
                import re

                match = re.search(r"成功同步 (\d+) 个", log.message)
                if match:
                    total_accounts += int(match.group(1))
            elif "同步失败" in log.message or "失败" in log.message:
                failed_count += 1

        # 构建合并后的消息
        merged_message = (
            f"批量同步所有账户: 成功 {success_count} 个实例，失败 {failed_count} 个实例，共同步 {total_accounts} 个账户"
        )

        # 构建详细信息
        details_parts = [
            f"开始时间: {start_log.created_at}",
            f"结束时间: {end_time}",
            f"持续时间: {duration:.2f}ms",
            f"状态码: {status_code}",
            f"总实例数: {total_instances}",
            f"成功实例数: {success_count}",
            f"失败实例数: {failed_count}",
            f"同步账户总数: {total_accounts}",
            f"原始日志数量: {len(sync_logs)}",
        ]

        # 添加响应信息
        if hasattr(response, "get_data"):
            try:
                response_data = response.get_data(as_text=True)
                if response_data and len(response_data) > 0:
                    # 不限制字符数，完整显示响应内容
                    details_parts.append(f"响应内容: {response_data}")
                else:
                    details_parts.append("响应内容: (空)")
            except Exception as e:
                details_parts.append(f"响应内容: (获取失败: {str(e)})")

        details = ", ".join(details_parts)

        # 确定日志级别
        log_level = "warning" if status_code >= 400 or failed_count > 0 else "info"
        levels = [start_log.level, log_level.upper()]
        level_priority = {"CRITICAL": 5, "ERROR": 4, "WARNING": 3, "INFO": 2, "DEBUG": 1}
        max_level = max(levels, key=lambda x: level_priority.get(x, 0))

        # 确定日志来源
        log_source = determine_log_source()

        # 创建合并后的日志
        merged_log = Log(
            level=max_level,
            log_type="batch_sync",
            module="batch_sync_handler",
            message=merged_message,
            details=details,
            user_id=current_user.id if current_user and hasattr(current_user, "id") else None,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            source=log_source,
        )

        db.session.add(merged_log)
        db.session.flush()  # 获取ID

        # 手动设置创建时间为开始日志的时间
        merged_log.created_at = start_log.created_at

        return merged_log

    except Exception as e:
        print(f"DEBUG: 合并批量同步日志失败: {e}")
        import traceback

        traceback.print_exc()
        return None


def _merge_regular_request_logs(start_log: Log, end_time: datetime, duration: float, status_code: int, response: Response) -> None:
    """合并普通请求日志"""
    try:
        # 创建合并后的日志
        merged_message = f"请求: {request.method} {request.path}"

        # 确定最严重的级别
        log_level = "warning" if status_code >= 400 else "info"
        levels = [start_log.level, log_level.upper()]
        level_priority = {"CRITICAL": 5, "ERROR": 4, "WARNING": 3, "INFO": 2, "DEBUG": 1}
        max_level = max(levels, key=lambda x: level_priority.get(x, 0))

        # 构建详细的响应信息
        response_size = response.content_length or 0
        response_headers = dict(response.headers)

        # 构建详细信息
        details_parts = [
            f"开始时间: {start_log.created_at}",
            f"结束时间: {end_time}",
            f"持续时间: {duration:.2f}ms",
            f"状态码: {status_code}",
            f"响应大小: {response_size} bytes",
            f"请求头: {dict(request.headers)}",
            f"响应头: {response_headers}",
        ]

        # 如果有响应体，尝试记录（不限制长度）
        try:
            if hasattr(response, "get_data"):
                response_data = response.get_data(as_text=True)
                if response_data and len(response_data) > 0:
                    # 不限制字符数，完整显示响应内容
                    details_parts.append(f"响应内容: {response_data}")
                else:
                    details_parts.append("响应内容: (空)")
        except Exception as e:
            print(f"DEBUG: 获取响应内容失败: {e}")
            details_parts.append(f"响应内容: (获取失败: {str(e)})")

        details = ", ".join(details_parts)

        # 确定日志来源
        log_source = determine_log_source()

        # 保存合并后的日志
        merged_log = Log(
            level=max_level,
            log_type="request",
            module="request_handler",
            message=merged_message,
            details=details,
            user_id=current_user.id if current_user and hasattr(current_user, "id") else None,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            source=log_source,
        )

        db.session.add(merged_log)
        db.session.flush()  # 获取ID

        # 手动设置创建时间为开始日志的时间
        merged_log.created_at = start_log.created_at

        return merged_log

    except Exception as e:
        print(f"DEBUG: 合并普通请求日志失败: {e}")
        import traceback

        traceback.print_exc()
        return None
