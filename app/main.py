import os
import sys
import time
from datetime import timezone, datetime

# 设置 UTC 时区（在所有其他导入之前）
os.environ['TZ'] = 'UTC'
try:
    time.tzset()  # 在非 Windows 系统上需要这行
except AttributeError:
    pass  # Windows 系统不支持 time.tzset()

# 确保当前时区是 UTC
datetime.now().astimezone(timezone.utc)

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_dir)

import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from fastapi import FastAPI
from app.routers.api import init_app
from app.config.settings import settings
from app.config.logging_config import setup_logging
from pkg.core.context.context_vars import set_app
from pkg.core.timezone import setup_utc_timezone

# 使用我们之前创建的时区设置函数
setup_utc_timezone()

# 设置应用名称
set_app(settings.APP_NAME)

# 设置日志
setup_logging()

app = FastAPI()
init_app(app)

async def main():
    """Main async function to run both timer and server"""
   
    # 配置服务器
    config = Config()
    config.bind = [f"{settings.HOST}:{settings.PORT}"]
    config.use_reloader = True
    config.workers = settings.WORKERS
    config.accesslog = "-"

    # 同时运行服务器
    await serve(app, config)

if __name__ == "__main__":
    asyncio.run(main())