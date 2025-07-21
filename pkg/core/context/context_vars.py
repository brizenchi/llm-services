from contextvars import ContextVar
from typing import Optional
import uuid

# 创建上下文变量
trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')
app_var: ContextVar[str] = ContextVar('app', default='')

def get_trace_id() -> str:
    """获取当前trace_id"""
    return trace_id_var.get() or str(uuid.uuid4())

def set_trace_id(trace_id: Optional[str] = None) -> None:
    """设置trace_id"""
    trace_id_var.set(trace_id or str(uuid.uuid4()))

def clear_trace_id() -> None:
    """清除trace_id"""
    trace_id_var.set('')

def get_app() -> str:
    """获取当前app名称"""
    return app_var.get()

def set_app(app: str) -> None:
    """设置app名称"""
    app_var.set(app)

def clear_app() -> None:
    """清除app名称"""
    app_var.set('') 