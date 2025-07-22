import time
from fastapi import Request, Response
import logging
import json
from typing import Any
from pkg.core.context.context_vars import get_trace_id
from starlette.types import Message
from starlette.datastructures import MutableHeaders
from copy import deepcopy
from fastapi.responses import StreamingResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("request_logger")

def format_json(obj: Any, indent_level: int = 0) -> str:
    """
    格式化JSON字符串，使其更易读
    
    Args:
        obj: 要格式化的对象
        indent_level: 缩进级别
    """
    try:
        if isinstance(obj, str):
            try:
                # 尝试解析JSON字符串
                data = json.loads(obj)
                return format_json(data, indent_level)
            except:
                # 处理普通字符串，美化显示
                return format_string(obj, indent_level)
        elif isinstance(obj, (dict, list)):
            # 使用json.dumps进行格式化，确保中文正确显示
            return json.dumps(obj, indent=2, ensure_ascii=False)
        else:
            return str(obj)
    except Exception as e:
        return f"<Error formatting object: {str(e)}>"

def format_string(s: str, indent_level: int = 0) -> str:
    """
    格式化字符串，处理特殊字符和换行
    
    Args:
        s: 要格式化的字符串
        indent_level: 缩进级别
    """
    indent = "  " * indent_level
    
    # 处理转义字符
    s = s.replace("\\n", "\n" + indent)  # 处理换行
    s = s.replace("\\t", "\t")           # 处理制表符
    s = s.replace("\\\"", "\"")          # 处理引号
    s = s.replace("\\\\", "\\")          # 处理反斜杠
    
    # 处理多行文本
    if "\n" in s:
        lines = s.split("\n")
        # 对于多行文本，每行都添加缩进
        return "\n".join(indent + line for line in lines)
    
    return indent + s

def format_headers(headers: dict) -> str:
    """格式化请求/响应头"""
    formatted = []
    for key, value in sorted(headers.items()):
        if key.lower() not in ["authorization", "cookie"]:  # 排除敏感头部
            formatted.append(f"  {key}: {value}")
    return "\n".join(formatted)

async def log_request_middleware(request: Request, call_next):
    """Middleware to log request and response details"""
    trace_id = get_trace_id()
    start_time = time.perf_counter()
    
    # 构建请求日志
    log_sections = [
        f"{'='*50}",
        "📝 请求信息",
        f"Trace ID: {trace_id}",
        f"路径: {request.url.path}",
        f"方法: {request.method}",
        f"查询参数: {str(request.query_params)}",
        f"客户端: {request.client.host if request.client else 'Unknown'}"
    ]
    
    # 如果是POST/PUT请求，记录请求体
    if request.method in ["POST", "PUT"]:
        try:
            body = await request.body()
            if body:
                body_str = body.decode()
                log_sections.append("请求体:")
                log_sections.append(format_json(body_str, indent_level=1))
        except Exception as e:
            log_sections.append(f"读取请求体错误: {str(e)}")
    
    # 记录请求信息
    logger.info("\n" + "\n".join(log_sections) + f"\n{'='*50}")
    
    # 调用下一个中间件或路由处理器
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.perf_counter() - start_time
    
    # 构建响应日志
    log_sections = [
        f"{'='*50}",
        "📬 响应信息",
        f"Trace ID: {trace_id}",
        f"状态码: {response.status_code}",
        f"处理时间: {process_time:.4f}s",
        "响应头:",
        format_headers(dict(response.headers))
    ]
    
    # 检查是否是流式响应
    is_stream = isinstance(response, StreamingResponse) or "text/event-stream" in response.headers.get("content-type", "")
    
    if is_stream:
        # 对于流式响应，只记录基本信息
        log_sections.append("响应体: <Stream Response>")
        logger.info("\n" + "\n".join(log_sections) + f"\n{'='*50}")
        return response
    else:
        try:
            # 创建一个新的响应对象来记录响应体
            response_body = []
            async for chunk in response.body_iterator:
                response_body.append(chunk)
            
            # 重建响应体
            body = b"".join(response_body)
            
            # 记录响应体内容
            if body:
                log_sections.append("响应体:")
                try:
                    # 尝试解析为JSON
                    body_content = json.loads(body)
                    log_sections.append(format_json(body_content, indent_level=1))
                except:
                    # 如果不是JSON，则作为普通文本处理
                    log_sections.append(format_string(body.decode(), indent_level=1))
            
            # 记录响应信息
            logger.info("\n" + "\n".join(log_sections) + f"\n{'='*50}")
            
            # 返回新的响应对象
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
        except Exception as e:
            logger.error(f"处理响应时出错: {str(e)}")
            # 如果处理响应时出错，返回原始响应
            return response