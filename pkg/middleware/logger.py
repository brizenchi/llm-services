import time
from fastapi import Request
import logging
import json
from typing import Any
from pkg.core.context.context_vars import get_trace_id
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("request_logger")

async def log_request_middleware(request: Request, call_next):
    """Middleware to log request and response details"""
    trace_id = get_trace_id()
    # 记录请求开始时间
    start_time = time.perf_counter()
    
    # 获取请求信息
    request_info = {
        "trace_id": trace_id,
        "path": request.url.path,
        "method": request.method,
        "query_params": str(request.query_params),
        "client_host": request.client.host if request.client else None,
    }
    
    # 如果是POST/PUT请求，记录请求体
    if request.method in ["POST", "PUT"]:
        try:
            body = await request.body()
            if body:
                request_info["body"] = body.decode()
        except Exception as e:
            request_info["body"] = f"Error reading body: {str(e)}"
    
    # 记录请求信息
    logger.info(f"[{trace_id}] Request: {json.dumps(request_info)}")
    
    # 调用下一个中间件或路由处理器
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.perf_counter() - start_time
    
    # 记录响应信息
    response_info = {
        "trace_id": trace_id,
        "status_code": response.status_code,
        "process_time": f"{process_time:.4f}s",
        "headers": dict(response.headers),
    }
    
    logger.info(f"[{trace_id}] Response: {json.dumps(response_info)}")
    
    return response