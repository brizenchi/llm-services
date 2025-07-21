from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
import asyncio
import logging
from .types import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    StreamResponse,
    ModelConfig,
    APIError
)

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """LLM客户端抽象基类"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self._available = True
    
    @abstractmethod
    async def chat_completion(
        self, 
        request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """
        执行聊天完成请求
        
        Args:
            request: 聊天完成请求
            
        Returns:
            聊天完成响应
            
        Raises:
            APIError: API调用失败
        """
        pass
    
    @abstractmethod
    async def chat_completion_stream(
        self, 
        request: ChatCompletionRequest
    ) -> AsyncGenerator[StreamResponse, None]:
        """
        执行流式聊天完成请求
        
        Args:
            request: 聊天完成请求
            
        Yields:
            流式响应数据
            
        Raises:
            APIError: API调用失败
        """
        pass
    
    def get_model(self) -> str:
        """获取模型名称"""
        return self.config.model
    
    def get_provider(self) -> str:
        """获取提供商名称"""
        return self.config.provider
    
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return self._available
    
    def set_available(self, available: bool) -> None:
        """设置客户端可用性"""
        self._available = available
    
    def get_config(self) -> ModelConfig:
        """获取模型配置"""
        return self.config
    
    async def _retry_request(self, request_func, *args, **kwargs):
        """
        带重试的请求执行
        
        Args:
            request_func: 请求函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            请求结果
            
        Raises:
            APIError: 重试失败后抛出最后一次错误
        """
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                return await request_func(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.max_retries} failed "
                    f"for model {self.config.model}: {e}"
                )
                
                if attempt < self.config.max_retries - 1:
                    # 指数退避
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                
        # 标记为不可用
        self.set_available(False)
        raise APIError(f"All {self.config.max_retries} attempts failed: {last_error}")


class BaseLLMClient(LLMClient):
    """基础LLM客户端实现"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._session = None
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def close(self):
        """关闭客户端连接"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _prepare_request_data(self, request: ChatCompletionRequest) -> dict:
        """
        准备请求数据
        
        Args:
            request: 聊天完成请求
            
        Returns:
            请求数据字典
        """
        data = {
            "model": request.model,
            "messages": [
                {"role": msg.role.value, "content": msg.content}
                for msg in request.messages
            ]
        }
        
        if request.max_tokens is not None:
            data["max_tokens"] = request.max_tokens
        
        if request.temperature is not None:
            data["temperature"] = request.temperature
        
        if request.stream is not None:
            data["stream"] = request.stream
        
        if request.stop is not None:
            data["stop"] = request.stop
        
        if request.functions is not None:
            data["functions"] = [
                {
                    "name": func.name,
                    "description": func.description,
                    "parameters": func.parameters
                }
                for func in request.functions
            ]
        
        return data
    
    def _get_headers(self) -> dict:
        """
        获取请求头
        
        Returns:
            请求头字典
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
    
    async def _validate_response(self, response_data: dict) -> None:
        """
        验证响应数据
        
        Args:
            response_data: 响应数据
            
        Raises:
            APIError: 响应无效时抛出
        """
        if "error" in response_data:
            error_msg = response_data["error"].get("message", "Unknown API error")
            raise APIError(f"API Error: {error_msg}")
        
        if "choices" not in response_data or not response_data["choices"]:
            raise APIError("Invalid response: no choices found") 