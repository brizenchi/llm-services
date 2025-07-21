import os
import time
from datetime import datetime, timezone
from functools import wraps
from app.config.settings import settings
def setup_utc_timezone():
    """设置系统时区为 UTC"""
    os.environ['TZ'] = settings.TIMEZONE
    try:
        time.tzset()  # 在非 Windows 系统上需要这行
    except AttributeError:
        # Windows 系统不支持 time.tzset()
        pass

def get_utc_now():
    """获取当前 UTC 时间"""
    return datetime.now(timezone.utc)

def format_utc_datetime(dt, format="%Y-%m-%d %H:%M:%S"):
    """格式化 UTC 时间"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(format)

def ensure_utc(func):
    """装饰器：确保函数中的 datetime 操作使用 UTC 时区"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 在函数执行前确保使用 UTC 时区
        old_tz = os.environ.get('TZ')
        os.environ['TZ'] = 'UTC'
        try:
            time.tzset()
        except AttributeError:
            pass
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # 恢复原来的时区设置
            if old_tz is not None:
                os.environ['TZ'] = old_tz
                try:
                    time.tzset()
                except AttributeError:
                    pass
    
    return wrapper

# 在模块导入时自动设置 UTC 时区
setup_utc_timezone() 