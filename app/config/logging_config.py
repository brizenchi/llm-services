import os
import logging.config
from datetime import datetime
from .settings import settings
from pkg.core.logging.formatters import JSONFormatter

def setup_logging():
    """配置日志"""
    # 确保日志目录存在
    log_dir = settings.LOG_DIR
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 生成日志文件路径
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{settings.LOG_FILE_NAME}.{current_date}")

    # 日志配置
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': JSONFormatter,
            },
        },
        'handlers': {
            'console': {
                'level': settings.LOG_LEVEL,
                'formatter': 'json',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            },
            'file': {
                'level': settings.LOG_LEVEL,
                'formatter': 'json',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': log_file,
                'when': 'midnight',  # 每天午夜切换文件
                'interval': 1,
                'backupCount': 30,  # 保留30天的日志
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['console', 'file'],
                'level': settings.LOG_LEVEL,
                'propagate': True,
                "app": settings.APP_NAME
            }
        }
    }
    
    logging.config.dictConfig(logging_config) 