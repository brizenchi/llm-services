from fastapi import FastAPI
from pkg.middleware.process_time import add_process_time_header
from pkg.middleware.logger import log_request_middleware
from pkg.middleware.trace_id import add_trace_id
from pkg.middleware.auth import add_auth_middleware
def register_middleware(app: FastAPI):
    """Register all middleware for the application"""
    
    @app.middleware("http")
    async def process_time_middleware(request, call_next):
        return await add_process_time_header(request, call_next)

    @app.middleware("http")
    async def request_logger_middleware(request, call_next):
        return await log_request_middleware(request, call_next)
    
    @app.middleware("http")
    async def trace_id_middleware(request, call_next):
        return await add_trace_id(request, call_next)

    @app.middleware("http")
    async def auth_middleware(request, call_next):
        return await add_auth_middleware(request, call_next)