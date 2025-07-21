from typing import Optional, Any
from pydantic import BaseModel
from pkg.core.context.context_vars import get_trace_id

class Result(BaseModel):
    code: int = 200
    message: str = "ok"
    data: Optional[Any] = None
    trace_id: Optional[str] = None

class ErrorCode:
    SUCCESS = 200
    FAIL = -1

def success_result(data: Any = None, msg: str = "ok", code: int = ErrorCode.SUCCESS) -> Result:
    """
    返回成功结果
    
    Args:
        data: 返回数据
        msg: 成功消息
        code: 状态码
    """
    return Result(
        code=code,
        msg=msg,
        data=data,
        trace_id=get_trace_id()
    )

def error_result(msg: str, code: int = ErrorCode.FAIL) -> Result:
    """
    返回错误结果
    
    Args:
        msg: 错误消息
        code: 错误码
    """
    return Result(
        code=code,
        msg=msg,
        data=None,
        trace_id=get_trace_id()
    ) 