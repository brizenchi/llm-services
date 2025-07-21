import time
from fastapi import Request
import logging
import uuid  # Add this import
from pkg.core.context.context_vars import set_trace_id, clear_trace_id

logger = logging.getLogger(__name__)

async def add_trace_id(request: Request, call_next):
    """Middleware to add processing time and trace ID to response headers"""
    try:
        # Get trace ID from request headers if exists, otherwise generate new one
        trace_id = request.headers.get("trace_id", str(uuid.uuid4()))
        set_trace_id(trace_id)
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time
        
        response.headers["X-Process-Time"] = str(process_time)
        # response.headers["X-Trace-ID"] = trace_id  # Add trace ID to response headers
        
        return response
    finally:
        clear_trace_id()  # 确保清理上下文