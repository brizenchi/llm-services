import json
import aiohttp
from typing import AsyncGenerator
import logging
from ..provider import BaseProvider
from ..client import BaseLLMClient
from ..types import (
    ModelConfig,
    ProviderConfig,
    ChatCompletionRequest,
    ChatCompletionResponse,
    StreamResponse,
    APIError,
    MessageRole,
    Message
)

logger = logging.getLogger(__name__)


class DeepSeekClient(BaseLLMClient):
    """DeepSeek模型客户端实现"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.deepseek.com/v1"
        self.chat_url = f"{self.base_url}/chat/completions"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self._get_headers()
            )
        return self._session
    
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """执行DeepSeek聊天完成请求"""
        return await self._retry_request(self._chat_completion_impl, request)
    
    async def _chat_completion_impl(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """实际的聊天完成请求实现"""
        session = await self._get_session()
        data = self._prepare_request_data(request)
        data['stream'] = False  # 确保非流式
        
        try:
            async with session.post(self.chat_url, json=data) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    raise APIError(f"HTTP {response.status}: {response_data}")
                
                await self._validate_response(response_data)
                return ChatCompletionResponse.from_dict(response_data)
                
        except aiohttp.ClientError as e:
            raise APIError(f"Request failed: {e}")
    
    async def chat_completion_stream(
        self, 
        request: ChatCompletionRequest
    ) -> AsyncGenerator[StreamResponse, None]:
        """执行DeepSeek流式聊天完成请求"""
        session = await self._get_session()
        data = self._prepare_request_data(request)
        data['stream'] = True  # 确保流式
        
        try:
            async with session.post(self.chat_url, json=data) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise APIError(f"HTTP {response.status}: {error_data}")
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    
                    if not line:
                        continue
                    
                    if line.startswith('data: '):
                        line = line[6:]  # 移除 'data: ' 前缀
                    
                    if line == '[DONE]':
                        break
                    
                    try:
                        chunk_data = json.loads(line)
                        yield StreamResponse.from_dict(chunk_data)
                    except json.JSONDecodeError:
                        continue  # 跳过无法解析的行
                        
        except aiohttp.ClientError as e:
            raise APIError(f"Stream request failed: {e}")


class DeepSeekProvider(BaseProvider):
    """DeepSeek Provider实现"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
    
    def create_client(self, model_config: ModelConfig) -> DeepSeekClient:
        """创建DeepSeek客户端实例"""
        return DeepSeekClient(model_config)
    
    @classmethod
    def create_from_config(
        cls,
        provider_name: str = "deepseek",
        models_config: dict = None
    ) -> 'DeepSeekProvider':
        """
        从配置字典创建DeepSeek Provider
        
        Args:
            provider_name: Provider名称
            models_config: 模型配置字典
            
        Returns:
            DeepSeek Provider实例
        """
        if models_config is None:
            models_config = {}
        
        models = {}
        for model_name, config in models_config.items():
            models[model_name] = ModelConfig(
                model=config.get('model', model_name),
                provider=provider_name,
                api_key=config['api_key'],
                base_url=config.get('base_url', 'https://api.deepseek.com/v1'),
                timeout=config.get('timeout', 30.0),
                max_retries=config.get('max_retries', 3),
                max_concurrent_calls=config.get('max_concurrent_calls', 10)
            )
        
        provider_config = ProviderConfig(
            provider=provider_name,
            models=models
        )
        
        return cls(provider_config)
    
    @classmethod
    def create_simple(
        cls,
        api_key: str,
        model_name: str = "deepseek-chat",
        base_url: str = None
    ) -> 'DeepSeekProvider':
        """
        创建简单的DeepSeek Provider配置
        
        Args:
            api_key: DeepSeek API密钥
            model_name: 模型名称
            base_url: API基础URL
            
        Returns:
            DeepSeek Provider实例
        """
        model_config = ModelConfig(
            model=model_name,
            provider="deepseek",
            api_key=api_key,
            base_url=base_url or "https://api.deepseek.com/v1"
        )
        
        provider_config = ProviderConfig(
            provider="deepseek",
            models={model_name: model_config}
        )
        
        return cls(provider_config) 