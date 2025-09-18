"""
泰摸鱼吧 - 本地开发环境启动文件
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault("FLASK_APP", "app")
os.environ.setdefault("FLASK_ENV", "development")

# 导入Flask应用
from app import create_app  # noqa: E402


def main() -> None:
    """主函数"""
    # 创建Flask应用
    app = create_app()

    # 获取配置
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"

    # 配置日志
    from app.utils.structlog_config import get_system_logger

    logger = get_system_logger()

    logger.info("=" * 50)
    logger.info("🐟 泰摸鱼吧 - 本地开发环境")
    logger.info("=" * 50)
    logger.info("🌐 访问地址: http://%s:%s", host, port)
    logger.info("🔑 默认登录: admin/Admin123!")
    logger.info("📊 管理界面: http://%s:%s/admin", host, port)
    logger.info("🔧 调试模式: %s", "开启" if debug else "关闭")
    logger.info("=" * 50)
    logger.info("按 Ctrl+C 停止服务器")
    logger.info("=" * 50)

    # 启动Flask应用
    # 在debug模式下禁用reloader以避免重复启动调度器
    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
