from dataclasses import dataclass
from app.config.settings import settings

@dataclass
class MySQLConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str = 'utf8mb4'
    pool_size: int = 10

    def __init__(self, source_name: str = 'default', ):
        """
        从settings中初始化MySQL配置
        Args:
            source_name: 数据源名称，对应settings.DATASOURCES中的键
        """
        config = settings.DATASOURCES.get(source_name)
        if not config:
            raise ValueError(f"Database source '{source_name}' not found in settings")

        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 3306)
        self.user = config.get('user')
        self.password = config.get('password')
        self.database = config.get('database')
        self.charset = config.get('charset', self.charset)
        self.pool_size = config.get('pool_size', self.pool_size)

        # 验证必要的配置
        required_fields = ['user', 'password', 'database']
        missing_fields = [field for field in required_fields if not getattr(self, field)]
        if missing_fields:
            raise ValueError(f"Missing required MySQL configuration fields: {', '.join(missing_fields)}") 