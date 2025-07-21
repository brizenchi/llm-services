from typing import Dict
from pkg.core.mysql.mysql_store import MySQLStore

class MySQLFactory:
    _instances: Dict[str, MySQLStore] = {}
    
    @classmethod
    def get_instance(cls, source_name: str = "default") -> MySQLStore:
        """获取指定数据源的实例"""
        if source_name not in cls._instances:
            cls._instances[source_name] = MySQLStore(source_name)
        return cls._instances[source_name]