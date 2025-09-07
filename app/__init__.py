"""
泰摸鱼吧 - Flask应用初始化
基于Flask的DBA数据库管理Web应用
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_cors import CORS
from celery import Celery
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()
jwt = JWTManager()
bcrypt = Bcrypt()
login_manager = LoginManager()
cors = CORS()

# 初始化Celery
celery = Celery()

def create_app(config_name=None):
    """
    创建Flask应用实例
    
    Args:
        config_name: 配置名称，默认为None
        
    Returns:
        Flask: Flask应用实例
    """
    app = Flask(__name__)
    
    # 配置应用
    configure_app(app, config_name)
    
    # 初始化扩展
    initialize_extensions(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 配置日志
    configure_logging(app)
    
    # 配置错误处理
    configure_error_handlers(app)
    
    return app

def configure_app(app, config_name):
    """
    配置Flask应用
    
    Args:
        app: Flask应用实例
        config_name: 配置名称
    """
    # 基础配置
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
    
    # 数据库配置
    database_url = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URI')
    if not database_url:
        # 默认使用SQLite，使用绝对路径
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        db_path = project_root / 'userdata' / 'taifish_dev.db'
        database_url = f'sqlite:///{db_path.absolute()}'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 根据数据库类型设置不同的引擎选项
    if database_url.startswith('sqlite'):
        # SQLite配置
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'connect_args': {'check_same_thread': False}
        }
    else:
        # PostgreSQL/MySQL配置
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_timeout': 20,
            'max_overflow': 0
        }
    
    # 缓存配置
    cache_type = os.getenv('CACHE_TYPE', 'simple')
    app.config['CACHE_TYPE'] = cache_type
    
    if cache_type == 'redis':
        app.config['CACHE_REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    app.config['CACHE_DEFAULT_TIMEOUT'] = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
    
    # 安全配置
    app.config['BCRYPT_LOG_ROUNDS'] = int(os.getenv('BCRYPT_LOG_ROUNDS', 12))
    
    # 文件上传配置
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'userdata/uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))
    
    # 日志配置
    app.config['LOG_LEVEL'] = os.getenv('LOG_LEVEL', 'INFO')
    app.config['LOG_FILE'] = os.getenv('LOG_FILE', 'userdata/logs/app.log')
    app.config['LOG_MAX_SIZE'] = int(os.getenv('LOG_MAX_SIZE', 10485760))
    app.config['LOG_BACKUP_COUNT'] = int(os.getenv('LOG_BACKUP_COUNT', 5))
    
    # 外部数据库配置
    app.config['SQL_SERVER_HOST'] = os.getenv('SQL_SERVER_HOST', 'localhost')
    app.config['SQL_SERVER_PORT'] = int(os.getenv('SQL_SERVER_PORT', 1433))
    app.config['SQL_SERVER_USERNAME'] = os.getenv('SQL_SERVER_USERNAME', 'sa')
    app.config['SQL_SERVER_PASSWORD'] = os.getenv('SQL_SERVER_PASSWORD', '')
    
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
    app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))
    app.config['MYSQL_USERNAME'] = os.getenv('MYSQL_USERNAME', 'root')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
    
    app.config['ORACLE_HOST'] = os.getenv('ORACLE_HOST', 'localhost')
    app.config['ORACLE_PORT'] = int(os.getenv('ORACLE_PORT', 1521))
    app.config['ORACLE_SERVICE_NAME'] = os.getenv('ORACLE_SERVICE_NAME', 'ORCL')
    app.config['ORACLE_USERNAME'] = os.getenv('ORACLE_USERNAME', 'system')
    app.config['ORACLE_PASSWORD'] = os.getenv('ORACLE_PASSWORD', '')

def initialize_extensions(app):
    """
    初始化Flask扩展
    
    Args:
        app: Flask应用实例
    """
    # 初始化数据库
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 初始化缓存
    cache.init_app(app)
    
    # 初始化JWT
    jwt.init_app(app)
    
    # 初始化密码加密
    bcrypt.init_app(app)
    
    # 初始化登录管理
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    
    # 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # 初始化CORS
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 初始化Celery (仅在Redis可用时)
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    try:
        import redis
        redis_client = redis.from_url(redis_url)
        redis_client.ping()
        # Redis可用，配置Celery
        celery.conf.update(
            broker_url=redis_url,
            result_backend=redis_url,
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=30 * 60,  # 30分钟
            task_soft_time_limit=25 * 60,  # 25分钟
            worker_prefetch_multiplier=1,
            worker_max_tasks_per_child=1000,
        )
        app.logger.info("Celery配置完成 (Redis可用)")
    except Exception as e:
        app.logger.warning(f"Redis不可用，跳过Celery配置: {e}")
        redis_client = None
        # Redis不可用，使用内存作为broker
        celery.conf.update(
            broker_url='memory://',
            result_backend='cache+memory://',
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=30 * 60,  # 30分钟
            task_soft_time_limit=25 * 60,  # 25分钟
            worker_prefetch_multiplier=1,
            worker_max_tasks_per_child=1000,
        )
    
    # 将redis_client添加到应用上下文
    app.redis_client = redis_client

def register_blueprints(app):
    """
    注册Flask蓝图
    
    Args:
        app: Flask应用实例
    """
    # 导入蓝图
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.instances import instances_bp
    from app.routes.credentials import credentials_bp
    from app.routes.accounts import accounts_bp
    from app.routes.tasks import tasks_bp
    from app.routes.params import params_bp
    from app.routes.logs import logs_bp
    from app.routes.dashboard import dashboard_bp
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(instances_bp, url_prefix='/instances')
    app.register_blueprint(credentials_bp, url_prefix='/credentials')
    app.register_blueprint(accounts_bp, url_prefix='/accounts')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(params_bp, url_prefix='/params')
    app.register_blueprint(logs_bp, url_prefix='/logs')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

def configure_logging(app):
    """
    配置日志系统
    
    Args:
        app: Flask应用实例
    """
    if not app.debug and not app.testing:
        # 创建日志目录
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 配置文件日志处理器
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_SIZE'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.info('泰摸鱼吧应用启动')

def configure_error_handlers(app):
    """
    配置错误处理器
    
    Args:
        app: Flask应用实例
    """
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not Found', 'message': '请求的资源不存在'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal Server Error', 'message': '服务器内部错误'}, 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return {'error': 'Forbidden', 'message': '访问被拒绝'}, 403
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        return {'error': 'Unauthorized', 'message': '未授权访问'}, 401

# 创建应用实例
app = create_app()

# 导入模型（确保模型被注册）
from app.models import user, instance, credential, account, task, log, global_param

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
