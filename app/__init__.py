"""
泰摸鱼吧 - Flask应用初始化
基于Flask的DBA数据库管理Web应用
"""

from app.constants import SystemConstants, DefaultConfig
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
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
csrf = CSRFProtect()

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
    
    # 配置会话安全
    configure_session_security(app)
    
    # 初始化扩展
    initialize_extensions(app)
    
    # 注册蓝图
    register_blueprints(app)
    
    # 配置日志
    configure_logging(app)
    
    # 注册全局错误处理器
    from app.utils.error_handler import register_error_handlers
    register_error_handlers(app)
    
    # 注册高级错误处理器
    from app.utils.advanced_error_handler import advanced_error_handler, handle_advanced_errors
    app.advanced_error_handler = advanced_error_handler
    
    # 注册高级错误处理器到Flask应用
    @app.errorhandler(Exception)
    def handle_advanced_exception(error):
        """全局高级错误处理"""
        from app.utils.advanced_error_handler import ErrorContext
        context = ErrorContext(error)
        error_response = advanced_error_handler.handle_error(error, context)
        
        # 根据错误类型返回适当的响应
        if hasattr(error, 'code'):
            status_code = error.code
        else:
            status_code = 500
            
        return jsonify(error_response), status_code
    
    # 性能监控已移除
    
    # 配置模板过滤器
    configure_template_filters(app)
    
    return app

def configure_app(app, config_name):
    """
    配置Flask应用
    
    Args:
        app: Flask应用实例
        config_name: 配置名称
    """
    # 基础配置
    secret_key = os.getenv('SECRET_KEY')
    jwt_secret_key = os.getenv('JWT_SECRET_KEY')
    
    if not secret_key:
        if app.debug:
            secret_key = 'dev-secret-key-change-in-production'
        else:
            raise ValueError("SECRET_KEY environment variable must be set in production")
    
    if not jwt_secret_key:
        if app.debug:
            jwt_secret_key = 'dev-jwt-secret-change-in-production'
        else:
            raise ValueError("JWT_SECRET_KEY environment variable must be set in production")
    
    app.config['SECRET_KEY'] = secret_key
    app.config['JWT_SECRET_KEY'] = jwt_secret_key
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

def configure_session_security(app):
    """
    配置会话安全
    
    Args:
        app: Flask应用实例
    """
    # 会话配置
    app.config['PERMANENT_SESSION_LIFETIME'] = SystemConstants.SESSION_LIFETIME  # 会话1小时过期
    app.config['SESSION_COOKIE_SECURE'] = not app.debug  # 生产环境使用HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止XSS攻击
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF保护
    
    # 防止会话固定攻击
    app.config['SESSION_COOKIE_NAME'] = 'taifish_session'
    
    # 会话超时配置
    app.config['SESSION_TIMEOUT'] = SystemConstants.SESSION_LIFETIME  # 1小时

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
    
    # 初始化缓存管理器
    from app.utils.cache_manager import init_cache_manager
    init_cache_manager(cache)
    
    # 初始化CSRF保护
    csrf.init_app(app)
    
    # 初始化JWT
    jwt.init_app(app)
    
    # 初始化密码加密
    bcrypt.init_app(app)
    
    # 初始化登录管理
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    
    # 会话安全配置
    login_manager.session_protection = "basic"  # 基础会话保护
    login_manager.remember_cookie_duration = SystemConstants.SESSION_LIFETIME  # 记住我功能1小时过期
    login_manager.remember_cookie_secure = not app.debug  # 生产环境使用HTTPS
    login_manager.remember_cookie_httponly = True  # 防止XSS攻击
    
    # 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # 初始化CORS
    allowed_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5001,http://127.0.0.1:5001').split(',')
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-CSRFToken"],
            "supports_credentials": True
        }
    })
    
    # 初始化CSRF保护
    csrf.init_app(app)
    
    # 初始化Celery (仅在Redis可用时)
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    try:
        import redis
        redis_client = redis.from_url(redis_url)
        
        # 初始化速率限制器
        from app.utils.rate_limiter import init_rate_limiter
        init_rate_limiter(redis_client)
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
    from app.routes.logs import logs_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.health import health_bp
    from app.routes.admin import admin_bp
    from app.routes.account_classification import account_classification_bp
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(instances_bp, url_prefix='/instances')
    app.register_blueprint(credentials_bp, url_prefix='/credentials')
    app.register_blueprint(accounts_bp, url_prefix='/accounts')
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    app.register_blueprint(logs_bp, url_prefix='/logs')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(health_bp, url_prefix='/health')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(account_classification_bp, url_prefix='/account-classification')

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
    配置错误处理器 - 已移除，使用统一的错误处理器
    """
    pass

def configure_template_filters(app):
    """
    配置模板过滤器
    
    Args:
        app: Flask应用实例
    """
    from app.utils.timezone import format_china_time
    
    @app.template_filter('china_time')
    def china_time_filter(dt, format_str='%Y-%m-%d %H:%M:%S'):
        """东八区时间格式化过滤器"""
        return format_china_time(dt, format_str)
    
    @app.template_filter('china_date')
    def china_date_filter(dt):
        """东八区日期格式化过滤器"""
        return format_china_time(dt, '%Y-%m-%d')
    
    @app.template_filter('china_datetime')
    def china_datetime_filter(dt):
        """东八区日期时间格式化过滤器"""
        return format_china_time(dt, '%Y-%m-%d %H:%M:%S')

# 创建应用实例
app = create_app()

# 导入模型（确保模型被注册）
from app.models import user, instance, credential, account, task, log, global_param

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=8000)
