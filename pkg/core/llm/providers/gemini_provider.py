import asyncio
import time
from typing import AsyncGenerator, Dict, Any, List
import logging
from google import genai
from google.genai import types

# 在文件顶部，修改相对导入为绝对导入（仅用于测试）
if __name__ == "__main__":
    import sys
    import os
    # 添加项目根目录到Python路径
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
    
    # 使用绝对导入
    from pkg.core.llm.provider import BaseProvider
    from pkg.core.llm.client import BaseLLMClient
    from pkg.core.llm.types import (
        ModelConfig, ProviderConfig, ChatCompletionRequest,
        ChatCompletionResponse, StreamResponse, APIError,
        MessageRole, Message, Choice, Usage, StreamChoice
    )
else:
    # 正常的相对导入
    from ..provider import BaseProvider
    from ..client import BaseLLMClient
    from ..types import (
        ModelConfig, ProviderConfig, ChatCompletionRequest,
        ChatCompletionResponse, StreamResponse, APIError,
        MessageRole, Message, Choice, Usage, StreamChoice
    )

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Gemini模型客户端实现 - 使用官方 Google GenAI SDK"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        # 初始化官方 genai 客户端
        self.client = genai.Client(api_key=config.api_key)
        self.model_name = config.model
    
    def _convert_messages_to_genai_format(self, messages: List[Message]) -> str:
        """将消息列表转换为 GenAI 格式的内容字符串"""
        # 如果只有一个用户消息，直接返回内容
        if len(messages) == 1 and messages[0].role == MessageRole.USER:
            return messages[0].content
        
        # 多轮对话需要构建上下文
        content_parts = []
        for message in messages:
            if message.role == MessageRole.SYSTEM:
                content_parts.append(f"System: {message.content}")
            elif message.role == MessageRole.USER:
                content_parts.append(f"User: {message.content}")
            elif message.role == MessageRole.ASSISTANT:
                content_parts.append(f"Assistant: {message.content}")
        
        return "\n".join(content_parts)
    
    def _convert_genai_response_to_openai_format(self, genai_response, model_name: str) -> ChatCompletionResponse:
        """将 GenAI 响应转换为标准格式"""
        try:
            # 获取响应文本
            response_text = genai_response.text
            
            # 构建Choice对象
            choice = Choice(
                index=0,
                message=Message(
                    role=MessageRole.ASSISTANT,
                    content=response_text
                ),
                finish_reason="stop"
            )
            
            # 构建Usage对象 (GenAI可能不提供详细的token使用信息)
            usage = Usage(
                prompt_tokens=0,  # GenAI SDK 可能不提供
                completion_tokens=0,  # GenAI SDK 可能不提供
                total_tokens=0
            )
            
            return ChatCompletionResponse(
                id=f"genai-{hash(response_text)}",
                object="chat.completion",
                created=int(time.time()),
                model=model_name,
                choices=[choice],
                usage=usage
            )
        except Exception as e:
            raise APIError(f"Failed to convert GenAI response: {e}")
    
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """执行聊天完成请求 - 使用官方 GenAI SDK"""
        return await self._retry_request(self._chat_completion_impl, request)
    
    async def _chat_completion_impl(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """实际的聊天完成请求实现"""
        try:
            # 转换消息格式
            contents = self._convert_messages_to_genai_format(request.messages)
            
            # 构建生成配置
            generation_config = types.GenerateContentConfig(
                temperature=request.temperature if request.temperature is not None else 0.7,
                top_p=request.top_p if request.top_p is not None else 0.8,
                max_output_tokens=request.max_tokens if request.max_tokens else 2048,
                thinking_config=types.ThinkingConfig(thinking_budget=0)  # 禁用思考模式
            )
            
            # 在异步上下文中运行同步的 GenAI 调用
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=generation_config
                )
            )
            
            return self._convert_genai_response_to_openai_format(response, request.model)
            
        except Exception as e:
            logger.error(f"GenAI request failed: {e}")
            raise APIError(f"GenAI request failed: {e}")
    
    async def chat_completion_stream(
        self, 
        request: ChatCompletionRequest
    ) -> AsyncGenerator[StreamResponse, None]:
        """执行流式聊天完成请求"""
        try:
            # 转换消息格式
            contents = self._convert_messages_to_genai_format(request.messages)
            
            # 构建生成配置
            generation_config = types.GenerateContentConfig(
                temperature=request.temperature if request.temperature is not None else 0.7,
                top_p=request.top_p if request.top_p is not None else 0.8,
                max_output_tokens=request.max_tokens if request.max_tokens else 2048,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
            
            # 在异步上下文中运行同步的流式调用
            loop = asyncio.get_event_loop()
            
            def generate_stream():
                return self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=generation_config
                )
            
            stream = await loop.run_in_executor(None, generate_stream)
            
            # 处理流式响应
            for chunk in stream:
                try:
                    if hasattr(chunk, 'text') and chunk.text:
                        choice = StreamChoice(
                            delta=Message(
                                role=MessageRole.ASSISTANT,
                                content=chunk.text
                            ),
                            index=0,
                            finish_reason=None
                        )
                        
                        yield StreamResponse(
                            id=f"genai-stream-{hash(chunk.text)}",
                            object="chat.completion.chunk",
                            created=int(time.time()),
                            model=request.model,
                            choices=[choice]
                        )
                except Exception as e:
                    logger.warning(f"Failed to process stream chunk: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"GenAI stream request failed: {e}")
            raise APIError(f"GenAI stream request failed: {e}")


class GeminiProvider(BaseProvider):
    """Gemini Provider实现 - 使用官方 Google GenAI SDK"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
    
    def create_client(self, model_config: ModelConfig) -> GeminiClient:
        """创建Gemini客户端实例"""
        return GeminiClient(model_config)
    
    @classmethod
    def create_from_config(
        cls,
        provider_name: str = "gemini",
        models_config: dict = None
    ) -> 'GeminiProvider':
        """从配置字典创建Gemini Provider"""
        if models_config is None:
            models_config = {}
        
        models = {}
        for model_name, config in models_config.items():
            models[model_name] = ModelConfig(
                model=config.get('model', model_name),
                provider=provider_name,
                api_key=config['api_key'],
                base_url=config.get('base_url', 'https://generativelanguage.googleapis.com/v1beta'),
                timeout=config.get('timeout', 30.0),
                max_retries=config.get('max_retries', 3),
                max_concurrent_calls=config.get('max_concurrent_calls', 10)
            )
        
        provider_config = ProviderConfig(
            provider=provider_name,
            models=models
        )
        
        # 创建Provider实例
        provider = cls(provider_config)
        
        # 手动创建并注册客户端
        for model_name, model_config in models.items():
            client = provider.create_client(model_config)
            provider.clients[model_name] = client  # 确保客户端被添加到clients字典中
            logger.info(f"Created client for model {model_name}")
        
        return provider
    
    @classmethod
    def create_simple(
        cls,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        base_url: str = None
    ) -> 'GeminiProvider':
        """
        创建简单的Gemini Provider配置
        
        Args:
            api_key: Gemini API密钥
            model_name: 模型名称
            base_url: API基础URL (GenAI SDK 会自动处理)
            
        Returns:
            Gemini Provider实例
        """
        model_config = ModelConfig(
            model=model_name,
            provider="gemini",
            api_key=api_key,
            base_url=base_url
        )
        
        provider_config = ProviderConfig(
            provider="gemini",
            models={model_name: model_config}
        )
        
        return cls(provider_config) 