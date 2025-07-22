from fastapi import APIRouter
from app.handler import user, demo
from app.routers.middleware import register_middleware

# 创建主路由
api_router = APIRouter()

# 注册所有子路由
api_router.include_router(user.router, prefix="/users")
api_router.include_router(demo.router, prefix="/demo")

def init_app(app):
    """Initialize the application with routes and middleware"""
    # 注册主路由
    app.include_router(api_router, prefix="/api/v1")
    # 注册中间件
    # register_middleware(app)