import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from pkg.core.llm import (
    LLMAggregator,
    Manager,
    get_manager,
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
    MessageRole,
    GeminiProvider,
    ModelConfig,
    ProviderConfig
)

logger = logging.getLogger(__name__)


class DemoService:
    """
    Demo服务 - 演示如何使用LLM架构调用Gemini模型
    """
    
    def __init__(self):
        self.manager: Manager = get_manager()
        self.aggregator: Optional[LLMAggregator] = None
        self._initialized = False
    
    async def initialize(self, gemini_config: Dict[str, Any]) -> None:
        """初始化Demo服务"""
        if self._initialized:
            logger.info("DemoService already initialized")
            return
        
        try:
            # 创建Gemini Provider
            gemini_provider = GeminiProvider.create_from_config(
                provider_name="gemini",
                models_config=gemini_config.get("models", {})
            )
            
            # 调试：检查provider内部状态
            logger.info(f"Provider clients: {list(gemini_provider.clients.keys())}")
            for model_name, client in gemini_provider.clients.items():
                logger.info(f"Model {model_name} client available: {client.is_available()}")
            
            # 注册Provider到Manager
            self.manager.register_provider(gemini_provider)
            
            # 验证注册是否成功
            registered_providers = self.manager.get_all_providers()
            all_models = self.manager.get_all_models()
            
            logger.info(f"Registered providers: {registered_providers}")
            logger.info(f"Available models: {all_models}")
            
            self._initialized = True
            logger.info("DemoService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize DemoService: {e}")
            raise
    
    async def simple_chat(self, message: str, model: str = "gemini-2.5-flash") -> Dict[str, Any]:
        """简单聊天接口"""
        if not self._initialized:
            raise RuntimeError("DemoService not initialized")
        
        try:
            # 先检查模型是否存在
            available_models = self.manager.get_all_models()
            logger.info(f"Looking for model {model} in available models: {available_models}")
            
            # 创建聊天请求
            request = ChatCompletionRequest(
                model=model,
                messages=[
                    Message(role=MessageRole.USER, content=message)
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # 获取客户端
            client = self.manager.get_client_by_model(model)
            response = await client.chat_completion(request)
            
            return {
                "success": True,
                "user_message": message,
                "model": model,
                "response": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_message": message,
                "model": model
            }
    
    async def multi_turn_chat(self, messages: List[Dict[str, str]], model: str = "gemini-2.5-flash") -> Dict[str, Any]:
        """多轮对话接口"""
        if not self._initialized:
            raise RuntimeError("DemoService not initialized")
        
        try:
            # 转换消息格式
            chat_messages = []
            for msg in messages:
                role = MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
                chat_messages.append(Message(role=role, content=msg["content"]))
            
            # 创建聊天请求
            request = ChatCompletionRequest(
                model=model,
                messages=chat_messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            # 使用 manager 直接获取客户端
            client = self.manager.get_client_by_model(model)
            response = await client.chat_completion(request)
            
            return {
                "success": True,
                "conversation": messages,
                "model": model,
                "response": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Multi-turn chat failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "conversation": messages,
                "model": model
            }
    
    async def get_available_models(self) -> Dict[str, Any]:
        """
        获取可用模型列表
        
        Returns:
            可用模型信息
        """
        if not self._initialized:
            raise RuntimeError("DemoService not initialized")
        
        try:
            all_models = self.manager.get_all_models()
            providers = self.manager.get_all_providers()
            
            return {
                "success": True,
                "providers": list(providers),
                "models": all_models,
                "total_models": sum(len(models) for models in all_models.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def stream_chat(self, message: str, model: str = "gemini-2.5-flash") -> AsyncGenerator[Dict[str, Any], None]:
        """流式聊天接口"""
        if not self._initialized:
            raise RuntimeError("DemoService not initialized")
        
        try:
            # 先检查模型是否存在
            available_models = self.manager.get_all_models()
            logger.info(f"Looking for model {model} in available models: {available_models}")
            
            # 创建聊天请求
            request = ChatCompletionRequest(
                model=model,
                messages=[
                    Message(role=MessageRole.USER, content=message)
                ],
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )
            
            # 获取客户端并开始流式请求
            client = self.manager.get_client_by_model(model)
            
            # 初始化统计
            total_content = ""
            chunk_count = 0
            
            # 发送开始事件
            yield {
                "type": "start",
                "model": model,
                "user_message": message,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            async for stream_response in client.chat_completion_stream(request):
                chunk_count += 1
                
                # 获取当前chunk的内容
                if stream_response.choices and len(stream_response.choices) > 0:
                    choice = stream_response.choices[0]
                    if choice.delta and choice.delta.content:
                        content_chunk = choice.delta.content
                        total_content += content_chunk
                        
                        yield {
                            "type": "content",
                            "content": content_chunk,
                            "chunk_index": chunk_count,
                            "model": model,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                        
                        # 检查是否完成
                        if choice.finish_reason:
                            yield {
                                "type": "finish",
                                "finish_reason": choice.finish_reason,
                                "total_content": total_content,
                                "total_chunks": chunk_count,
                                "model": model,
                                "timestamp": asyncio.get_event_loop().time()
                            }
                            break
            
            # 如果没有收到finish信号，发送完成事件
            if chunk_count > 0:
                yield {
                    "type": "done",
                    "total_content": total_content,
                    "total_chunks": chunk_count,
                    "model": model,
                    "user_message": message,
                    "timestamp": asyncio.get_event_loop().time()
                }
            
        except Exception as e:
            logger.error(f"Stream chat failed: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "user_message": message,
                "model": model,
                "timestamp": asyncio.get_event_loop().time()
            }

    async def stream_multi_turn_chat(self, messages: List[Dict[str, str]], model: str = "gemini-2.5-flash") -> AsyncGenerator[Dict[str, Any], None]:
        """流式多轮对话接口"""
        if not self._initialized:
            raise RuntimeError("DemoService not initialized")
        
        try:
            # 转换消息格式
            chat_messages = []
            for msg in messages:
                role = MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
                chat_messages.append(Message(role=role, content=msg["content"]))
            
            # 创建聊天请求
            request = ChatCompletionRequest(
                model=model,
                messages=chat_messages,
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )
            
            # 获取客户端并开始流式请求
            client = self.manager.get_client_by_model(model)
            
            # 初始化统计
            total_content = ""
            chunk_count = 0
            
            # 发送开始事件
            yield {
                "type": "start",
                "model": model,
                "conversation": messages,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            async for stream_response in client.chat_completion_stream(request):
                chunk_count += 1
                
                # 获取当前chunk的内容
                if stream_response.choices and len(stream_response.choices) > 0:
                    choice = stream_response.choices[0]
                    if choice.delta and choice.delta.content:
                        content_chunk = choice.delta.content
                        total_content += content_chunk
                        
                        yield {
                            "type": "content",
                            "content": content_chunk,
                            "chunk_index": chunk_count,
                            "model": model,
                            "timestamp": asyncio.get_event_loop().time()
                        }
                        
                        # 检查是否完成
                        if choice.finish_reason:
                            yield {
                                "type": "finish",
                                "finish_reason": choice.finish_reason,
                                "total_content": total_content,
                                "total_chunks": chunk_count,
                                "model": model,
                                "timestamp": asyncio.get_event_loop().time()
                            }
                            break
            
            # 如果没有收到finish信号，发送完成事件
            if chunk_count > 0:
                yield {
                    "type": "done",
                    "total_content": total_content,
                    "total_chunks": chunk_count,
                    "model": model,
                    "conversation": messages,
                    "timestamp": asyncio.get_event_loop().time()
                }
            
        except Exception as e:
            logger.error(f"Stream multi-turn chat failed: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "conversation": messages,
                "model": model,
                "timestamp": asyncio.get_event_loop().time()
            }


# 全局实例
_demo_service = None


async def get_demo_service() -> DemoService:
    """
    获取Demo服务实例（单例模式）
    
    Returns:
        DemoService实例
    """
    global _demo_service
    if _demo_service is None:
        _demo_service = DemoService()
    return _demo_service


async def initialize_demo_service(gemini_config: Dict[str, Any]) -> None:
    """
    初始化Demo服务
    
    Args:
        gemini_config: Gemini配置
    """
    service = await get_demo_service()
    await service.initialize(gemini_config) 