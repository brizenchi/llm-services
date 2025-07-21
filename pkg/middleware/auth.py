import time
from fastapi import Request, Response
import logging
import uuid  # Add this import
from pkg.core.context.context_vars import set_trace_id, clear_trace_id
from fastapi import HTTPException
from app.config.settings import settings
from pkg.core.result.result import error_result
from fastapi.responses import JSONResponse
import json

logger = logging.getLogger(__name__)

async def add_auth_middleware(request: Request, call_next):
    """认证中间件，检查token权限"""
    try:
        # 定义不需要认证的路径
        skip_auth_paths = [
            "/api/v1/demo/health",
            "/api/v1/demo/debug",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
        
        # 检查是否需要跳过认证
        if request.url.path in skip_auth_paths:
            return await call_next(request)
        
        # 获取token - 支持多种格式
        token = ""
        
        # 优先检查 Authorization: Bearer <token> 格式
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # 去掉 "Bearer " 前缀
        else:
            # 兼容原有的 token 头格式
            token = request.headers.get("token", "")
        
        # 验证token
        if not token:
            result = error_result(msg="请提供访问令牌 (支持 Authorization: Bearer <token> 或 token: <token> 格式)", code=401)
            return JSONResponse(
                status_code=401,
                content=json.loads(result.model_dump_json())
            )
        
        if token != settings.TOKEN:
            result = error_result(msg="没权限", code=401)
            return JSONResponse(
                status_code=401,
                content=json.loads(result.model_dump_json())
            )
        
        return await call_next(request)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"认证中间件异常: {str(e)}")
        result = error_result(msg="认证服务异常", code=500)
        return JSONResponse(
            status_code=500,
            content=json.loads(result.model_dump_json())
        )