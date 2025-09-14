"""
泰摸鱼吧 - 数据库实例管理路由
"""

from typing import Any

from flask import Blueprint, Response, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models.account import Account
from app.models.credential import Credential
from app.models.instance import Instance
from app.services.database_service import DatabaseService
from app.utils.decorators import create_required, delete_required, update_required, view_required
from app.utils.security import (
    sanitize_form_data,
    validate_db_type,
    validate_required_fields,
)
from app.utils.structlog_config import get_api_logger, log_error, log_info, log_warning

# 创建蓝图
instances_bp = Blueprint("instances", __name__)

# 获取API日志记录器
api_logger = get_api_logger()


@instances_bp.route("/")
@login_required
@view_required
def index() -> str:
    """实例管理首页"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    search = request.args.get("search", "", type=str)
    db_type = request.args.get("db_type", "", type=str)
    environment = request.args.get("environment", "", type=str)

    # 构建查询
    query = Instance.query

    if search:
        query = query.filter(
            db.or_(
                Instance.name.contains(search),
                Instance.host.contains(search),
                Instance.description.contains(search),
            )
        )

    if db_type:
        query = query.filter(Instance.db_type == db_type)

    if environment:
        query = query.filter(Instance.environment == environment)

    # 分页查询
    instances = query.paginate(page=page, per_page=per_page, error_out=False)

    # 获取所有可用的凭据
    credentials = Credential.query.filter_by(is_active=True).all()

    # 获取数据库类型配置
    from app.services.database_type_service import DatabaseTypeService

    database_types = DatabaseTypeService.get_active_types()

    if request.is_json:
        return jsonify(
            {
                "instances": [instance.to_dict() for instance in instances.items],
                "pagination": {
                    "page": instances.page,
                    "pages": instances.pages,
                    "per_page": instances.per_page,
                    "total": instances.total,
                    "has_next": instances.has_next,
                    "has_prev": instances.has_prev,
                },
                "credentials": [cred.to_dict() for cred in credentials],
                "database_types": [db_type.to_dict() for db_type in database_types],
            }
        )

    return render_template(
        "instances/index.html",
        instances=instances,
        credentials=credentials,
        database_types=database_types,
        search=search,
        db_type=db_type,
        environment=environment,
    )


@instances_bp.route("/create", methods=["GET", "POST"])
@login_required
@create_required
def create() -> str | Response | tuple[Response, int]:
    """创建实例"""
    # 获取凭据列表
    credentials = Credential.query.filter_by(is_active=True).all()

    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form

        # 清理输入数据
        data = sanitize_form_data(data)

        # 输入验证
        required_fields = ["name", "db_type", "host", "port", "environment"]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            if request.is_json:
                return jsonify({"error": validation_error}), 400
            flash(validation_error, "error")
            return render_template("instances/create.html", credentials=credentials)

        # 验证数据库类型
        db_type_error = validate_db_type(data.get("db_type"))
        if db_type_error:
            if request.is_json:
                return jsonify({"error": db_type_error}), 400
            flash(db_type_error, "error")
            return render_template("instances/create.html", credentials=credentials)

        # 验证环境类型
        valid_environments = ["production", "development", "testing"]
        if data.get("environment") not in valid_environments:
            error_msg = "环境类型必须是生产环境、开发环境或测试环境"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            flash(error_msg, "error")
            return render_template("instances/create.html", credentials=credentials)

        # 验证端口号
        try:
            port = int(data.get("port"))
            if port < 1 or port > 65535:
                error_msg = "端口号必须在1-65535之间"
                raise ValueError(error_msg)
        except (ValueError, TypeError):
            error_msg = "端口号必须是1-65535之间的整数"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            flash(error_msg, "error")
            return render_template("instances/create.html", credentials=credentials)

        # 验证凭据ID
        if data.get("credential_id"):
            try:
                credential_id = int(data.get("credential_id"))
                credential = Credential.query.get(credential_id)
                if not credential:
                    error_msg = "凭据不存在"
                    raise ValueError(error_msg)
            except (ValueError, TypeError):
                error_msg = "无效的凭据ID"
                if request.is_json:
                    return jsonify({"error": error_msg}), 400
                flash(error_msg, "error")
                return render_template("instances/create.html", credentials=credentials)

        # 验证实例名称唯一性
        existing_instance = Instance.query.filter_by(name=data.get("name")).first()
        if existing_instance:
            error_msg = "实例名称已存在"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            flash(error_msg, "error")
            return render_template("instances/create.html", credentials=credentials)

        try:
            # 创建新实例
            instance = Instance(
                name=data.get("name").strip(),
                db_type=data.get("db_type"),
                host=data.get("host").strip(),
                port=int(data.get("port")),
                database_name=data.get("database_name", "").strip() or None,
                credential_id=(int(data.get("credential_id")) if data.get("credential_id") else None),
                description=data.get("description", "").strip(),
                environment=data.get("environment", "production"),
            )

            # 设置其他属性
            instance.is_active = data.get("is_active", True) in [True, "on", "1", 1]

            db.session.add(instance)
            db.session.commit()

            # 记录操作日志
            api_logger.info(
                "创建数据库实例",
                user_id=current_user.id,
                instance_id=instance.id,
                instance_name=instance.name,
                db_type=instance.db_type,
                host=instance.host,
            )

            if request.is_json:
                return (
                    jsonify({"message": "实例创建成功", "instance": instance.to_dict()}),
                    201,
                )

            flash("实例创建成功！", "success")
            return redirect(url_for("instances.index"))

        except Exception as e:
            db.session.rollback()
            log_error(f"创建实例失败: {e}", module="instances", exc_info=True)

            # 根据错误类型提供更具体的错误信息
            if "UNIQUE constraint failed" in str(e):
                error_msg = "实例名称已存在，请使用其他名称"
            elif "NOT NULL constraint failed" in str(e):
                error_msg = "必填字段不能为空"
            elif "FOREIGN KEY constraint failed" in str(e):
                error_msg = "关联的凭据不存在"
            else:
                error_msg = f"创建实例失败: {str(e)}"

            if request.is_json:
                return jsonify({"error": error_msg}), 500

            flash(error_msg, "error")

    # GET请求，显示创建表单
    credentials = Credential.query.filter_by(is_active=True).all()

    # 获取可用的数据库类型
    from app.services.database_type_service import DatabaseTypeService

    database_types = DatabaseTypeService.get_active_types()

    if request.is_json:
        return jsonify(
            {
                "credentials": [cred.to_dict() for cred in credentials],
                "database_types": [dt.to_dict() for dt in database_types],
            }
        )

    return render_template("instances/create.html", credentials=credentials, database_types=database_types)


@instances_bp.route("/test-connection", methods=["POST"])
@login_required
@view_required
def test_instance_connection() -> str | Response | tuple[Response, int]:
    """测试数据库连接"""
    try:
        # 添加调试日志
        log_info(f"收到测试连接请求，Content-Type: {request.content_type}", module="instances")
        log_info(f"请求数据: {request.get_data()}", module="instances")

        # 检查Content-Type
        if not request.is_json:
            log_warning(f"请求不是JSON格式，Content-Type: {request.content_type}", module="instances")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"请求必须是JSON格式，当前Content-Type: {request.content_type}",
                    }
                ),
                400,
            )

        data = request.get_json()

        # 添加调试日志
        log_info(f"解析后的JSON数据: {data}", module="instances")

        # 验证必需参数
        if not data:
            log_warning("测试连接请求参数为空", module="instances")
            return jsonify({"success": False, "error": "请求参数为空"}), 400

        required_fields = ["db_type", "host", "port", "credential_id"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"缺少必需参数: {', '.join(missing_fields)}",
                    }
                ),
                400,
            )

        # 验证端口号
        try:
            port = int(data.get("port", 0))
            if port <= 0 or port > 65535:
                return (
                    jsonify({"success": False, "error": "端口号必须在1-65535之间"}),
                    400,
                )
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "端口号必须是有效的数字"}), 400

        # 验证凭据ID
        try:
            credential_id = int(data.get("credential_id")) if data.get("credential_id") else None
            if credential_id and credential_id <= 0:
                return (
                    jsonify({"success": False, "error": "凭据ID必须是有效的正整数"}),
                    400,
                )
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "凭据ID必须是有效的数字"}), 400

        # 创建临时实例对象进行测试
        temp_instance = Instance(
            name=data.get("name", "test"),
            db_type=data.get("db_type"),
            host=data.get("host"),
            port=port,
            credential_id=credential_id,
            description="test",
        )

        # 获取凭据信息
        if temp_instance.credential_id:
            credential = Credential.query.get(temp_instance.credential_id)
            if not credential:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"凭据ID {temp_instance.credential_id} 不存在",
                        }
                    ),
                    400,
                )
            temp_instance.credential = credential
        else:
            return jsonify({"success": False, "error": "必须选择数据库凭据"}), 400

        # 使用数据库服务测试连接
        from app.services.database_service import DatabaseService

        db_service = DatabaseService()
        result = db_service.test_connection(temp_instance)

        return jsonify(result)

    except Exception as e:
        log_error(f"测试连接失败: {e}", module="instances")
        return jsonify({"success": False, "error": f"测试连接失败: {str(e)}"}), 500


@instances_bp.route("/<int:instance_id>")
@login_required
@view_required
def detail(instance_id: int) -> str | Response | tuple[Response, int]:
    """实例详情"""
    instance = Instance.query.get_or_404(instance_id)

    if request.is_json:
        return jsonify(instance.to_dict())

    return render_template("instances/detail.html", instance=instance)


@instances_bp.route("/statistics")
@login_required
@view_required
def statistics() -> str | Response:
    """实例统计页面"""
    stats = get_instance_statistics()

    if request.is_json:
        return jsonify(stats)

    return render_template("instances/statistics.html", stats=stats)


@instances_bp.route("/api/statistics")
@login_required
@view_required
def api_statistics() -> Response:
    """获取实例统计API"""
    stats = get_instance_statistics()
    return jsonify(stats)


@instances_bp.route("/<int:instance_id>/edit", methods=["GET", "POST"])
@login_required
@update_required
def edit(instance_id: int) -> str | Response | tuple[Response, int]:
    """编辑实例"""
    instance = Instance.query.get_or_404(instance_id)

    if request.method == "POST":
        data = request.get_json() if request.is_json else request.form

        # 清理输入数据
        data = sanitize_form_data(data)

        # 输入验证
        required_fields = ["name", "db_type", "host", "port", "environment"]
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            if request.is_json:
                return jsonify({"error": validation_error}), 400
            flash(validation_error, "error")
            return render_template("instances/edit.html", instance=instance)

        # 验证数据库类型
        db_type_error = validate_db_type(data.get("db_type"))
        if db_type_error:
            if request.is_json:
                return jsonify({"error": db_type_error}), 400
            flash(db_type_error, "error")
            return render_template("instances/edit.html", instance=instance)

        # 验证环境类型
        valid_environments = ["production", "development", "testing"]
        if data.get("environment") not in valid_environments:
            error_msg = "环境类型必须是生产环境、开发环境或测试环境"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            flash(error_msg, "error")
            return render_template("instances/edit.html", instance=instance)

        # 验证端口号
        try:
            port = int(data.get("port"))
            if port < 1 or port > 65535:
                error_msg = "端口号必须在1-65535之间"
                raise ValueError(error_msg)
        except (ValueError, TypeError):
            error_msg = "端口号必须是1-65535之间的整数"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            flash(error_msg, "error")
            return render_template("instances/edit.html", instance=instance)

        # 验证凭据ID
        if data.get("credential_id"):
            try:
                credential_id = int(data.get("credential_id"))
                credential = Credential.query.get(credential_id)
                if not credential:
                    error_msg = "凭据不存在"
                    raise ValueError(error_msg)
            except (ValueError, TypeError):
                error_msg = "无效的凭据ID"
                if request.is_json:
                    return jsonify({"error": error_msg}), 400
                flash(error_msg, "error")
                return render_template("instances/edit.html", instance=instance)

        # 验证实例名称唯一性（排除当前实例）
        existing_instance = Instance.query.filter(Instance.name == data.get("name"), Instance.id != instance_id).first()
        if existing_instance:
            error_msg = "实例名称已存在"
            if request.is_json:
                return jsonify({"error": error_msg}), 400
            flash(error_msg, "error")
            return render_template("instances/edit.html", instance=instance)

        try:
            # 更新实例信息
            instance.name = data.get("name", instance.name).strip()
            instance.db_type = data.get("db_type", instance.db_type)
            instance.host = data.get("host", instance.host).strip()
            instance.port = int(data.get("port", instance.port))
            instance.database_name = data.get("database_name", instance.database_name)
            if instance.database_name:
                instance.database_name = instance.database_name.strip() or None
            instance.environment = data.get("environment", instance.environment)
            instance.credential_id = int(data.get("credential_id")) if data.get("credential_id") else None
            instance.description = data.get("description", instance.description)
            if data.get("description"):
                instance.description = data.get("description").strip()
            # 正确处理布尔值
            is_active_value = data.get("is_active", instance.is_active)
            if isinstance(is_active_value, str):
                instance.is_active = is_active_value in ["on", "true", "1", "yes"]
            else:
                instance.is_active = bool(is_active_value)

            db.session.commit()

            # 记录操作日志
            log_info(
                "更新数据库实例",
                module="instances",
                user_id=current_user.id,
                instance_id=instance.id,
                instance_name=instance.name,
                db_type=instance.db_type,
                host=instance.host,
                changes={
                    "name": data.get("name"),
                    "db_type": data.get("db_type"),
                    "host": data.get("host"),
                    "port": data.get("port"),
                    "environment": data.get("environment"),
                    "credential_id": data.get("credential_id"),
                    "description": data.get("description"),
                    "is_active": data.get("is_active"),
                },
            )

            if request.is_json:
                return jsonify({"message": "实例更新成功", "instance": instance.to_dict()})

            flash("实例更新成功！", "success")
            return redirect(url_for("instances.detail", instance_id=instance_id))

        except Exception as e:
            db.session.rollback()
            log_error(f"更新实例失败: {e}", module="instances", exc_info=True)

            # 根据错误类型提供更具体的错误信息
            if "UNIQUE constraint failed" in str(e):
                error_msg = "实例名称已存在，请使用其他名称"
            elif "NOT NULL constraint failed" in str(e):
                error_msg = "必填字段不能为空"
            elif "FOREIGN KEY constraint failed" in str(e):
                error_msg = "关联的凭据不存在"
            else:
                error_msg = f"更新实例失败: {str(e)}"

            if request.is_json:
                return jsonify({"error": error_msg}), 500

            flash(error_msg, "error")

    # GET请求，显示编辑表单
    credentials = Credential.query.filter_by(is_active=True).all()

    # 获取可用的数据库类型
    from app.services.database_type_service import DatabaseTypeService

    database_types = DatabaseTypeService.get_active_types()

    if request.is_json:
        return jsonify(
            {
                "instance": instance.to_dict(),
                "credentials": [cred.to_dict() for cred in credentials],
                "database_types": [dt.to_dict() for dt in database_types],
            }
        )

    return render_template(
        "instances/edit.html", instance=instance, credentials=credentials, database_types=database_types
    )


@instances_bp.route("/<int:instance_id>/delete", methods=["POST"])
@login_required
@delete_required
def delete(instance_id: int) -> str | Response | tuple[Response, int]:
    """删除实例"""
    instance = Instance.query.get_or_404(instance_id)

    try:
        # 记录操作日志
        log_info(
            "删除数据库实例",
            module="instances",
            user_id=current_user.id,
            instance_id=instance.id,
            instance_name=instance.name,
            db_type=instance.db_type,
            host=instance.host,
        )

        # 级联删除相关数据
        # 1. 删除账户信息
        accounts_count = instance.accounts.count()
        if accounts_count > 0:
            instance.accounts.delete()
            log_info(f"删除了 {accounts_count} 个账户记录", module="instances")

        # 2. 删除同步数据
        sync_data_count = instance.sync_data.count()
        if sync_data_count > 0:
            instance.sync_data.delete()
            log_info(f"删除了 {sync_data_count} 条同步数据记录", module="instances")

        # 3. 删除实例本身
        db.session.delete(instance)
        db.session.commit()

        log_info(f"实例 {instance.name} 及其相关数据删除成功", module="instances")

        if request.is_json:
            return jsonify(
                {
                    "message": "实例删除成功",
                    "deleted_accounts": accounts_count,
                    "deleted_sync_data": sync_data_count,
                }
            )

        flash(
            f"实例删除成功！已删除 {accounts_count} 个账户和 {sync_data_count} 条同步数据",
            "success",
        )
        return redirect(url_for("instances.index"))

    except Exception as e:
        db.session.rollback()
        log_error(f"删除实例失败: {e}", module="instances")

        if request.is_json:
            return jsonify({"error": "删除实例失败，请重试"}), 500

        flash("删除实例失败，请重试", "error")
        return redirect(url_for("instances.index"))


@instances_bp.route("/batch-delete", methods=["POST"])
@login_required
@delete_required
def batch_delete() -> str | Response | tuple[Response, int]:
    """批量删除实例"""
    try:
        data = request.get_json()
        instance_ids = data.get("instance_ids", [])

        if not instance_ids:
            return jsonify({"success": False, "error": "请选择要删除的实例"}), 400

        # 检查是否有账户关联
        account_counts = {}
        for instance_id in instance_ids:
            instance = Instance.query.get(instance_id)
            if instance:
                count = instance.accounts.count()
                if count > 0:
                    account_counts[instance.name] = count

        if account_counts:
            error_msg = "以下实例无法删除，还有账户关联：\n"
            for name, count in account_counts.items():
                error_msg += f"- {name}: {count} 个账户\n"
            return jsonify({"success": False, "error": error_msg.strip()}), 400

        # 批量删除
        deleted_count = 0
        deleted_accounts = 0
        deleted_sync_data = 0

        for instance_id in instance_ids:
            instance = Instance.query.get(instance_id)
            if instance:
                # 记录操作日志
                log_info(
                    "批量删除数据库实例",
                    module="instances",
                    user_id=current_user.id,
                    instance_id=instance.id,
                    instance_name=instance.name,
                    db_type=instance.db_type,
                    host=instance.host,
                )

                # 删除相关数据
                accounts_count = instance.accounts.count()
                sync_data_count = instance.sync_data.count()

                if accounts_count > 0:
                    instance.accounts.delete()
                    deleted_accounts += accounts_count

                if sync_data_count > 0:
                    instance.sync_data.delete()
                    deleted_sync_data += sync_data_count

                # 删除实例本身
                db.session.delete(instance)
                deleted_count += 1

        db.session.commit()

        log_info(
            f"批量删除完成：{deleted_count} 个实例，{deleted_accounts} 个账户，{deleted_sync_data} 条同步数据",
            module="instances",
        )

        return jsonify(
            {
                "success": True,
                "message": f"成功删除 {deleted_count} 个实例",
                "deleted_count": deleted_count,
                "deleted_accounts": deleted_accounts,
                "deleted_sync_data": deleted_sync_data,
            }
        )

    except Exception as e:
        db.session.rollback()
        log_error(f"批量删除实例失败: {e}", module="instances")
        return jsonify({"success": False, "error": f"批量删除实例失败: {str(e)}"}), 500


@instances_bp.route("/batch-create", methods=["POST"])
@login_required
@create_required
def batch_create() -> str | Response | tuple[Response, int]:
    """批量创建实例"""
    try:
        # 检查是否有文件上传
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename.endswith(".csv"):
                return _process_csv_file(file)
            return jsonify({"success": False, "error": "请上传CSV格式文件"}), 400

        # 处理JSON格式（保持向后兼容）
        data = request.get_json()
        instances_data = data.get("instances", [])

        if not instances_data:
            return jsonify({"success": False, "error": "请提供实例数据"}), 400

        return _process_instances_data(instances_data)

    except Exception as e:
        db.session.rollback()
        log_error(f"批量创建实例失败: {e}", module="instances")
        return jsonify({"success": False, "error": f"批量创建实例失败: {str(e)}"}), 500


def _process_csv_file(file: Any) -> dict[str, Any] | Response | tuple[Response, int]:
    """处理CSV文件"""
    import csv
    import io

    try:
        # 读取CSV文件
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.DictReader(stream)

        instances_data = []
        for row in csv_input:
            # 清理数据
            instance_data = {}
            for key, value in row.items():
                if value and value.strip():
                    instance_data[key.strip()] = value.strip()
                else:
                    instance_data[key.strip()] = None

            instances_data.append(instance_data)

        return _process_instances_data(instances_data)

    except Exception as e:
        return jsonify({"success": False, "error": f"CSV文件处理失败: {str(e)}"}), 400


def _process_instances_data(
    instances_data: list[dict[str, Any]],
) -> dict[str, Any] | Response | tuple[Response, int]:
    """处理实例数据"""
    created_count = 0
    errors = []

    for i, instance_data in enumerate(instances_data):
        try:
            # 验证必填字段
            required_fields = ["name", "db_type", "host", "port"]
            for field in required_fields:
                if not instance_data.get(field):
                    errors.append(f"第 {i + 1} 个实例缺少必填字段: {field}")
                    continue

            if errors:
                continue

            # 检查实例名称是否已存在
            existing_instance = Instance.query.filter_by(name=instance_data["name"]).first()
            if existing_instance:
                errors.append(f"第 {i + 1} 个实例名称已存在: {instance_data['name']}")
                continue

            # 处理端口号
            try:
                port = int(instance_data["port"])
            except (ValueError, TypeError):
                errors.append(f"第 {i + 1} 个实例端口号无效: {instance_data['port']}")
                continue

            # 处理凭据ID
            credential_id = None
            if instance_data.get("credential_id"):
                try:
                    credential_id = int(instance_data["credential_id"])
                except (ValueError, TypeError):
                    errors.append(f"第 {i + 1} 个实例凭据ID无效: {instance_data['credential_id']}")
                    continue

            # 创建实例
            instance = Instance(
                name=instance_data["name"],
                db_type=instance_data["db_type"],
                host=instance_data["host"],
                port=port,
                database_name=instance_data.get("database_name"),
                environment=instance_data.get("environment", "production"),
                description=instance_data.get("description"),
                credential_id=credential_id,
                tags={},
            )

            db.session.add(instance)
            created_count += 1

            # 记录操作日志
            log_info(
                "批量创建数据库实例",
                module="instances",
                user_id=current_user.id,
                instance_name=instance.name,
                db_type=instance.db_type,
                host=instance.host,
                environment=instance.environment,
            )

        except Exception as e:
            errors.append(f"第 {i + 1} 个实例创建失败: {str(e)}")
            continue

    if created_count > 0:
        db.session.commit()

    if errors:
        return jsonify(
            {
                "success": True,
                "message": f"成功创建 {created_count} 个实例",
                "created_count": created_count,
                "errors": errors,
            }
        )
    return jsonify(
        {
            "success": True,
            "message": f"成功创建 {created_count} 个实例",
            "created_count": created_count,
        }
    )


@instances_bp.route("/export")
@login_required
@view_required
def export_instances() -> Response:
    """导出实例数据为CSV"""
    import csv
    import io
    from datetime import datetime

    from flask import Response

    # 获取查询参数（与index方法保持一致）
    search = request.args.get("search", "", type=str)
    db_type = request.args.get("db_type", "", type=str)
    environment = request.args.get("environment", "", type=str)

    # 构建查询（与index方法保持一致）
    query = Instance.query

    if search:
        query = query.filter(
            db.or_(
                Instance.name.contains(search),
                Instance.host.contains(search),
                Instance.description.contains(search),
            )
        )

    if db_type:
        query = query.filter(Instance.db_type == db_type)

    if environment:
        query = query.filter(Instance.environment == environment)

    # 获取所有实例数据
    instances = query.all()

    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    writer.writerow(
        [
            "ID",
            "实例名称",
            "数据库类型",
            "主机地址",
            "端口",
            "数据库名",
            "环境",
            "状态",
            "描述",
            "凭据ID",
            "同步次数",
            "最后连接时间",
            "创建时间",
            "更新时间",
        ]
    )

    # 写入实例数据
    for instance in instances:
        writer.writerow(
            [
                instance.id,
                instance.name,
                instance.db_type,
                instance.host,
                instance.port,
                instance.database_name or "",
                instance.environment,
                "启用" if instance.is_active else "禁用",
                instance.description or "",
                instance.credential_id or "",
                instance.sync_count or 0,
                instance.last_connected.strftime("%Y-%m-%d %H:%M:%S") if instance.last_connected else "",
                instance.created_at.strftime("%Y-%m-%d %H:%M:%S") if instance.created_at else "",
                instance.updated_at.strftime("%Y-%m-%d %H:%M:%S") if instance.updated_at else "",
            ]
        )

    # 创建响应
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"instances_export_{timestamp}.csv"

    response = Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

    return response


@instances_bp.route("/template/download")
@login_required
@view_required
def download_template() -> Response:
    """下载CSV模板"""
    import csv
    import io

    from flask import Response

    # 创建CSV内容
    output = io.StringIO()
    writer = csv.writer(output)

    # 写入表头
    writer.writerow(
        [
            "name",
            "db_type",
            "host",
            "port",
            "database_name",
            "environment",
            "description",
            "credential_id",
        ]
    )

    # 写入示例数据
    writer.writerow(
        [
            "mysql-prod-01",
            "mysql",
            "192.168.1.100",
            "3306",
            "mysql",
            "production",
            "生产环境MySQL主库",
            "1",
        ]
    )
    writer.writerow(
        [
            "mysql-dev-01",
            "mysql",
            "192.168.1.101",
            "3306",
            "mysql",
            "development",
            "开发环境MySQL",
            "2",
        ]
    )
    writer.writerow(
        [
            "postgres-test-01",
            "postgresql",
            "192.168.1.102",
            "5432",
            "postgres",
            "testing",
            "测试环境PostgreSQL",
            "3",
        ]
    )

    # 创建响应
    output.seek(0)
    response = Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=instances_template.csv"},
    )

    return response


@instances_bp.route("/<int:instance_id>/test", methods=["POST"])
@login_required
@view_required
def test_connection(instance_id: int) -> str | Response | tuple[Response, int]:
    """测试数据库连接"""
    instance = Instance.query.get_or_404(instance_id)

    try:
        # 使用数据库服务测试连接
        db_service = DatabaseService()
        result = db_service.test_connection(instance)

        if result["success"]:
            # 更新最后连接时间
            instance.last_connected = db.func.now()
            db.session.commit()

            if request.is_json:
                return jsonify({"message": "连接测试成功", "result": result})

            flash("连接测试成功！", "success")
        else:
            if request.is_json:
                return jsonify({"error": "连接测试失败", "result": result}), 400

            flash(f"连接测试失败: {result.get('error', '未知错误')}", "error")

    except Exception as e:
        log_error(f"测试连接失败: {e}", module="instances")

        if request.is_json:
            return jsonify({"error": "连接测试失败，请重试"}), 500

        flash("连接测试失败，请重试", "error")

    return redirect(url_for("instances.detail", instance_id=instance_id))


@instances_bp.route("/<int:instance_id>/sync", methods=["POST"])
@login_required
@update_required
def sync_accounts(instance_id: int) -> str | Response | tuple[Response, int]:
    """同步账户信息"""
    instance = Instance.query.get_or_404(instance_id)

    try:
        # 记录操作开始日志
        log_info(
            "开始同步账户",
            module="instances",
            user_id=current_user.id,
            instance_id=instance.id,
            instance_name=instance.name,
            db_type=instance.db_type,
            host=instance.host,
        )

        # 使用数据库服务同步账户
        db_service = DatabaseService()
        result = db_service.sync_accounts(instance)

        if result["success"]:
            # 增加同步次数计数
            instance.sync_count = (instance.sync_count or 0) + 1
            db.session.commit()

            # 记录操作成功日志
            log_info(
                "账户同步成功",
                module="instances",
                user_id=current_user.id,
                instance_id=instance.id,
                instance_name=instance.name,
                db_type=instance.db_type,
                host=instance.host,
                synced_count=result.get("synced_count", 0),
                sync_count=instance.sync_count,
            )

            if request.is_json:
                return jsonify({"message": "账户同步成功", "result": result})

            flash("账户同步成功！", "success")
        else:
            # 记录操作失败日志
            log_error(
                "账户同步失败",
                module="instances",
                user_id=current_user.id,
                instance_id=instance.id,
                instance_name=instance.name,
                db_type=instance.db_type,
                host=instance.host,
                error=result.get("error", "未知错误"),
            )

            if request.is_json:
                return jsonify({"error": "账户同步失败", "result": result}), 400

            flash(f"账户同步失败: {result.get('error', '未知错误')}", "error")

    except Exception as e:
        log_error(f"同步账户失败: {e}", module="instances", instance_id=instance.id)

        # 记录操作异常日志
        log_error(
            "账户同步异常",
            module="instances",
            user_id=current_user.id,
            instance_id=instance.id,
            instance_name=instance.name,
            db_type=instance.db_type,
            host=instance.host,
            error=str(e),
        )

        if request.is_json:
            return jsonify({"error": "账户同步失败，请重试"}), 500

        flash("账户同步失败，请重试", "error")

    # 如果是AJAX请求，返回JSON响应
    if request.is_json:
        return jsonify({"error": "同步失败，请重试"}), 500

    return redirect(url_for("instances.detail", instance_id=instance_id))


# API路由
@instances_bp.route("/api/instances")
@login_required
@view_required
def api_list() -> Response:
    """获取实例列表API"""
    instances = Instance.query.filter_by(is_active=True).all()
    return jsonify([instance.to_dict() for instance in instances])


@instances_bp.route("/api/instances/<int:instance_id>")
@login_required
@view_required
def api_detail(instance_id: int) -> Response:
    """获取实例详情API"""
    instance = Instance.query.get_or_404(instance_id)
    return jsonify(instance.to_dict())


@instances_bp.route("/api/instances/<int:instance_id>/test")
@login_required
@view_required
def api_test_connection(instance_id: int) -> Response | tuple[Response, int]:
    """测试连接API"""
    instance = Instance.query.get_or_404(instance_id)

    try:
        db_service = DatabaseService()
        result = db_service.test_connection(instance)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@instances_bp.route("/api/test-connection", methods=["POST"])
@login_required
@view_required
def api_test_instance_connection() -> Response | tuple[Response, int]:
    """测试数据库连接API（无需CSRF）"""
    try:
        data = request.get_json()

        # 添加调试日志
        log_info(f"收到API测试连接请求，Content-Type: {request.content_type}", module="instances")
        log_info(f"请求数据: {request.get_data()}", module="instances")

        # 检查Content-Type
        if not request.is_json:
            log_warning(f"请求不是JSON格式，Content-Type: {request.content_type}", module="instances")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"请求必须是JSON格式，当前Content-Type: {request.content_type}",
                    }
                ),
                400,
            )

        # 添加调试日志
        log_info(f"解析后的JSON数据: {data}", module="instances")

        # 验证必需参数
        if not data:
            log_warning("测试连接请求参数为空", module="instances")
            return jsonify({"success": False, "error": "请求参数为空"}), 400

        required_fields = ["db_type", "host", "port", "credential_id"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"缺少必需参数: {', '.join(missing_fields)}",
                    }
                ),
                400,
            )

        # 验证端口号
        try:
            port = int(data.get("port", 0))
            if port <= 0 or port > 65535:
                return (
                    jsonify({"success": False, "error": "端口号必须在1-65535之间"}),
                    400,
                )
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "端口号必须是有效的数字"}), 400

        # 验证凭据ID
        try:
            credential_id = int(data.get("credential_id")) if data.get("credential_id") else None
            if credential_id and credential_id <= 0:
                return (
                    jsonify({"success": False, "error": "凭据ID必须是有效的正整数"}),
                    400,
                )
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "凭据ID必须是有效的数字"}), 400

        # 创建临时实例对象进行测试
        temp_instance = Instance(
            name=data.get("name", "test"),
            db_type=data.get("db_type"),
            host=data.get("host"),
            port=port,
            credential_id=credential_id,
            description="test",
        )

        # 获取凭据信息
        if temp_instance.credential_id:
            credential = Credential.query.get(temp_instance.credential_id)
            if not credential:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"凭据ID {temp_instance.credential_id} 不存在",
                        }
                    ),
                    400,
                )
            temp_instance.credential = credential
        else:
            return jsonify({"success": False, "error": "必须选择数据库凭据"}), 400

        # 使用数据库服务测试连接
        db_service = DatabaseService()
        result = db_service.test_connection(temp_instance)

        return jsonify(result)

    except Exception as e:
        log_error(f"测试连接失败: {e}", module="instances")
        return jsonify({"success": False, "error": f"测试连接失败: {str(e)}"}), 500


def get_instance_statistics() -> dict[str, Any]:
    """获取实例统计数据"""
    try:
        # 基础统计
        total_instances = Instance.query.count()
        active_instances = Instance.query.filter_by(is_active=True).count()
        inactive_instances = Instance.query.filter_by(is_active=False).count()

        # 数据库类型统计
        db_type_stats = (
            db.session.query(Instance.db_type, db.func.count(Instance.id).label("count"))
            .group_by(Instance.db_type)
            .all()
        )

        # 端口统计
        port_stats = (
            db.session.query(Instance.port, db.func.count(Instance.id).label("count"))
            .group_by(Instance.port)
            .order_by(db.func.count(Instance.id).desc())
            .limit(10)
            .all()
        )

        # 数据库版本统计（使用真实的版本信息）
        version_stats = (
            db.session.query(
                Instance.db_type,
                Instance.database_version,
                db.func.count(Instance.id).label("count"),
            )
            .group_by(Instance.db_type, Instance.database_version)
            .all()
        )

        # 转换为版本统计格式
        version_stats = [
            {
                "db_type": stat.db_type,
                "version": stat.database_version or "未知版本",
                "count": stat.count,
            }
            for stat in version_stats
        ]

        # 最近连接的实例（按最后连接时间排序）
        recent_connections = Instance.query.order_by(Instance.last_connected.desc().nullslast()).limit(10).all()

        # 数据库类型数量
        db_types_count = len(db_type_stats)

        return {
            "total_instances": total_instances,
            "active_instances": active_instances,
            "inactive_instances": inactive_instances,
            "db_types_count": db_types_count,
            "db_type_stats": [{"db_type": stat.db_type, "count": stat.count} for stat in db_type_stats],
            "port_stats": [{"port": stat.port, "count": stat.count} for stat in port_stats],
            "version_stats": version_stats,
            "recent_connections": recent_connections,
        }

    except Exception as e:
        log_error(f"获取实例统计失败: {e}", module="instances", exc_info=True)
        return {
            "total_instances": 0,
            "active_instances": 0,
            "inactive_instances": 0,
            "db_types_count": 0,
            "db_type_stats": [],
            "port_stats": [],
            "version_stats": [],
            "recent_connections": [],
        }


def get_default_version(db_type: str) -> str:
    """获取数据库类型的默认版本"""
    default_versions = {
        "postgresql": "15.x",
        "mysql": "8.0.x",
        "sqlserver": "2019",
        "oracle": "19c",
        "sqlite": "3.x",
    }
    return default_versions.get(db_type, "未知版本")


@instances_bp.route("/<int:instance_id>/accounts/<int:account_id>/permissions")
@login_required
@view_required
def get_account_permissions(instance_id: int, account_id: int) -> dict[str, Any] | Response | tuple[Response, int]:
    """获取账户权限详情"""
    instance = Instance.query.get_or_404(instance_id)
    account = Account.query.filter_by(id=account_id, instance_id=instance_id).first_or_404()

    try:
        from app.services.database_service import DatabaseService

        db_service = DatabaseService()

        # 获取账户权限
        permissions = db_service.get_account_permissions(instance, account)
        log_info(f"DEBUG API: 获取到的权限数据: {permissions}", module="instances")
        log_info(f"DEBUG API: 权限数据类型: {type(permissions)}", module="instances")

        response = {
            "success": True,
            "account": {
                "id": account.id,
                "username": account.username,
                "host": account.host,
                "plugin": account.plugin,
                "db_type": instance.db_type,
            },
            "permissions": permissions,
        }
        log_info(f"DEBUG API: 完整响应: {response}", module="instances")

        return jsonify(response)

    except Exception as e:
        log_error(f"获取账户权限失败: {e}", module="instances")
        return jsonify({"success": False, "error": f"获取权限失败: {str(e)}"}), 500
