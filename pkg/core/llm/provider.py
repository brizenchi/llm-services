from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging
from .types import (
    ModelConfig,
    ProviderConfig,
    ModelNotFoundError
)
from .client import LLMClient

logger = logging.getLogger(__name__)


class Provider(ABC):
    """LLM Provider抽象基类"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.clients: Dict[str, LLMClient] = {}
    
    @abstractmethod
    async def register_client(self, model_config: ModelConfig) -> None:
        """
        注册模型客户端
        
        Args:
            model_config: 模型配置
            
        Raises:
            Exception: 注册失败时抛出
        """
        pass
    
    @abstractmethod
    def create_client(self, model_config: ModelConfig) -> LLMClient:
        """
        创建模型客户端实例
        
        Args:
            model_config: 模型配置
            
        Returns:
            LLM客户端实例
        """
        pass
    
    def get_llm_client(self, model_name: str) -> LLMClient:
        """
        获取指定模型的客户端
        
        Args:
            model_name: 模型名称
            
        Returns:
            LLM客户端实例
            
        Raises:
            ModelNotFoundError: 模型不存在时抛出
        """
        if model_name not in self.clients:
            raise ModelNotFoundError(
                f"Model {model_name} not found for provider {self.config.provider}"
            )
        
        client = self.clients[model_name]
        if not client.is_available():
            logger.warning(f"Model {model_name} is marked as unavailable")
        
        return client
    
    def get_config(self) -> ProviderConfig:
        """获取Provider配置"""
        return self.config
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """
        获取指定模型的配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型配置，如果不存在则返回None
        """
        return self.config.get_model_config(model_name)
    
    def get_available_models(self) -> list[str]:
        """
        获取所有可用的模型列表
        
        Returns:
            可用模型名称列表
        """
        return [
            model_name for model_name, client in self.clients.items()
            if client.is_available()
        ]
    
    def get_provider_name(self) -> str:
        """获取Provider名称"""
        return self.config.provider
    
    async def health_check(self) -> Dict[str, bool]:
        """
        检查所有模型的健康状态
        
        Returns:
            模型名称到健康状态的映射
        """
        health_status = {}
        
        for model_name, client in self.clients.items():
            try:
                # 简单的健康检查 - 检查客户端是否可用
                health_status[model_name] = client.is_available()
            except Exception as e:
                logger.error(f"Health check failed for {model_name}: {e}")
                health_status[model_name] = False
                client.set_available(False)
        
        return health_status
    
    async def close(self):
        """关闭所有客户端连接"""
        for client in self.clients.values():
            try:
                if hasattr(client, 'close'):
                    await client.close()
            except Exception as e:
                logger.error(f"Error closing client: {e}")


class BaseProvider(Provider):
    """基础Provider实现"""
    
    async def register_client(self, model_config: ModelConfig) -> None:
        """
        注册模型客户端
        
        Args:
            model_config: 模型配置
        """
        try:
            client = self.create_client(model_config)
            self.clients[model_config.model] = client
            logger.info(
                f"Successfully registered model {model_config.model} "
                f"for provider {self.config.provider}"
            )
        except Exception as e:
            logger.error(
                f"Failed to register model {model_config.model}: {e}"
            )
            raise
    
    async def initialize_all_models(self) -> None:
        """初始化配置中的所有模型"""
        for model_name, model_config in self.config.models.items():
            try:
                await self.register_client(model_config)
            except Exception as e:
                logger.error(
                    f"Failed to initialize model {model_name}: {e}"
                )
                # 继续初始化其他模型，不因为一个模型失败而停止
                continue
    
    def create_client(self, model_config: ModelConfig) -> LLMClient:
        """
        创建模型客户端实例 - 子类需要实现此方法
        
        Args:
            model_config: 模型配置
            
        Returns:
            LLM客户端实例
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("Subclasses must implement create_client method") 