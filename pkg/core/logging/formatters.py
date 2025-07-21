import logging
import json
from datetime import datetime
from pkg.core.context.context_vars import get_trace_id, get_app

class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record):
        """格式化日志记录为JSON格式"""
        # 基础日志字段
        log_data = {
            "level": record.levelname.lower(),
            "msg": record.getMessage(),
            "time": datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
            "trace_id": get_trace_id(),
            "app": get_app()
        }
        
        # 如果有异常信息，添加到日志中
        if record.exc_info:
            log_data["error"] = self.formatException(record.exc_info)
            
        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
            
        return json.dumps(log_data, ensure_ascii=False)

def setup_logging():
    # 配置日志格式
    formatter = JSONFormatter(
        '%(asctime)s - %(trace_id)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 配置处理器
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO) 