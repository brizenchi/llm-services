import os
from typing import Dict, Any
from dotenv import load_dotenv
import base64
# 根据环境加载对应的 .env 文件
env = os.getenv("APP_ENV", "dev")
env_file = os.path.join("deployment", f".env.{env}" if env != "dev" else ".env")

# 加载环境变量
load_dotenv(env_file)

class Settings:
    # 服务配置
    APP_NAME: str = os.getenv("APP_NAME", "deeper-newsletter")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # 服务器配置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    TIMEZONE: str = os.getenv("TIMEZONE", "UTC")
   
    # 日志配置
    LOG_DIR: str = os.getenv('LOG_DIR', 'logs')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s [%(levelname)s] [%(trace_id)s] %(name)s: %(message)s')
    LOG_FILE_NAME: str = os.getenv('LOG_FILE_NAME', os.getenv('APP_NAME', 'app'))
  
    # OpenAI 配置
    LLM_MODEL = {
        "deepseek-chat": {
            "api_key": os.getenv('DEEPSEEK_API_KEY'),
            "base_url": os.getenv('DEEPSEEK_API_BASE_URL')
        },
        "gemini-2.5-flash": {
            "api_key": os.getenv('GEMINI_API_KEY'),
            "base_url": os.getenv('GEMINI_API_BASE_URL')
        }
    }
    
    
    @property
    def CHROMA_AUTH_TOKEN(self) -> str:
        credentials = f"{self.CHROMA_USERNAME}:{self.CHROMA_PASSWORD}"
        return base64.b64encode(credentials.encode()).decode()
    
    def dict(self) -> Dict[str, Any]:
        """返回所有配置的字典形式"""
        return {
            key: value for key, value in self.__class__.__dict__.items()
            if not key.startswith('_')
        }

settings = Settings()

