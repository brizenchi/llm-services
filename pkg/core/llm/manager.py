import threading
import asyncio
from typing import Dict, List, Optional, Union
import logging
from .types import (
    ModelConfig,
    ProviderConfig,
    ProviderNotFoundError,
    ModelNotFoundError
)
from .provider import Provider
from .client import LLMClient

logger = logging.getLogger(__name__)


class Manager:
    """LLM Manager管理所有Provider和模型客户端"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self.providers: Dict[str, Provider] = {}
        self._provider_lock = threading.RLock()
        self._initialized = True
        logger.info("LLM Manager initialized")
    
    def register_provider(self, provider: Provider) -> None:
        """
        注册Provider
        
        Args:
            provider: Provider实例
        """
        with self._provider_lock:
            provider_name = provider.get_provider_name()
            self.providers[provider_name] = provider
            logger.info(f"Provider {provider_name} registered successfully")
    
    def get_provider(self, provider_name: str) -> Provider:
        """
        获取指定的Provider
        
        Args:
            provider_name: Provider名称
            
        Returns:
            Provider实例
            
        Raises:
            ProviderNotFoundError: Provider不存在时抛出
        """
        with self._provider_lock:
            if provider_name not in self.providers:
                raise ProviderNotFoundError(f"Provider {provider_name} not found")
            return self.providers[provider_name]
    
    def must_get_provider(self, provider_name: str) -> Provider:
        """
        获取Provider，如果不存在则抛出异常
        
        Args:
            provider_name: Provider名称
            
        Returns:
            Provider实例
            
        Raises:
            ProviderNotFoundError: Provider不存在时抛出
        """
        return self.get_provider(provider_name)
    
    def get_llm_client(self, provider_name: str, model_name: str) -> LLMClient:
        """
        获取指定Provider和模型的客户端
        
        Args:
            provider_name: Provider名称
            model_name: 模型名称
            
        Returns:
            LLM客户端实例
            
        Raises:
            ProviderNotFoundError: Provider不存在时抛出
            ModelNotFoundError: 模型不存在时抛出
        """
        provider = self.get_provider(provider_name)
        return provider.get_llm_client(model_name)
    
    def get_all_providers(self) -> List[str]:
        """
        获取所有已注册的Provider名称
        
        Returns:
            Provider名称列表
        """
        with self._provider_lock:
            return list(self.providers.keys())
    
    def get_all_models(self) -> Dict[str, List[str]]:
        """
        获取所有Provider的模型列表
        
        Returns:
            Provider名称到模型名称列表的映射
        """
        with self._provider_lock:
            result = {}
            for provider_name, provider in self.providers.items():
                result[provider_name] = provider.get_available_models()
            return result
    
    def find_model_provider(self, model_name: str) -> Optional[str]:
        """
        查找指定模型所属的Provider
        
        Args:
            model_name: 模型名称
            
        Returns:
            Provider名称，如果未找到则返回None
        """
        with self._provider_lock:
            for provider_name, provider in self.providers.items():
                if model_name in provider.get_available_models():
                    return provider_name
            return None
    
    def get_client_by_model(self, model_name: str) -> LLMClient:
        """
        根据模型名称获取客户端（自动查找Provider）
        
        Args:
            model_name: 模型名称
            
        Returns:
            LLM客户端实例
            
        Raises:
            ModelNotFoundError: 模型不存在时抛出
        """
        provider_name = self.find_model_provider(model_name)
        if provider_name is None:
            raise ModelNotFoundError(f"Model {model_name} not found in any provider")
        
        return self.get_llm_client(provider_name, model_name)
    
    async def health_check_all(self) -> Dict[str, Dict[str, bool]]:
        """
        检查所有Provider和模型的健康状态
        
        Returns:
            Provider名称到模型健康状态映射的字典
        """
        result = {}
        
        with self._provider_lock:
            providers = list(self.providers.items())
        
        for provider_name, provider in providers:
            try:
                result[provider_name] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for provider {provider_name}: {e}")
                result[provider_name] = {}
        
        return result
    
    def clear(self) -> None:
        """清除所有已注册的Provider"""
        with self._provider_lock:
            self.providers.clear()
            logger.info("All providers cleared")
    
    async def close_all(self) -> None:
        """关闭所有Provider的连接"""
        with self._provider_lock:
            providers = list(self.providers.values())
        
        for provider in providers:
            try:
                await provider.close()
            except Exception as e:
                logger.error(f"Error closing provider {provider.get_provider_name()}: {e}")
        
        logger.info("All providers closed")
    
    def get_provider_config(self, provider_name: str) -> ProviderConfig:
        """
        获取Provider配置
        
        Args:
            provider_name: Provider名称
            
        Returns:
            Provider配置
            
        Raises:
            ProviderNotFoundError: Provider不存在时抛出
        """
        provider = self.get_provider(provider_name)
        return provider.get_config()
    
    def get_model_config(self, provider_name: str, model_name: str) -> ModelConfig:
        """
        获取模型配置
        
        Args:
            provider_name: Provider名称
            model_name: 模型名称
            
        Returns:
            模型配置
            
        Raises:
            ProviderNotFoundError: Provider不存在时抛出
            ModelNotFoundError: 模型不存在时抛出
        """
        provider = self.get_provider(provider_name)
        config = provider.get_model_config(model_name)
        if config is None:
            raise ModelNotFoundError(
                f"Model {model_name} not found in provider {provider_name}"
            )
        return config


def get_manager() -> Manager:
    """
    获取全局Manager实例
    
    Returns:
        Manager实例
    """
    return Manager()


def get_client(provider_name: str, model_name: str) -> LLMClient:
    """
    便捷函数：获取LLM客户端
    
    Args:
        provider_name: Provider名称
        model_name: 模型名称
        
    Returns:
        LLM客户端实例
    """
    manager = get_manager()
    return manager.get_llm_client(provider_name, model_name)


def get_client_by_model(model_name: str) -> LLMClient:
    """
    便捷函数：根据模型名称获取客户端
    
    Args:
        model_name: 模型名称
        
    Returns:
        LLM客户端实例
    """
    manager = get_manager()
    return manager.get_client_by_model(model_name) 