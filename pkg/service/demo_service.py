import logging
import asyncio
import json
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

def format_messages(messages: List[Message]) -> str:
    """格式化消息列表，使日志更易读"""
    formatted = []
    for msg in messages:
        formatted.append({
            "role": msg.role,
            "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        })
    return json.dumps(formatted, indent=2, ensure_ascii=False)

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

    async def simple_chat(
        self, 
        message: str, 
        model: str = "gemini-2.5-flash",
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """简单聊天接口"""
        if not self._initialized:
            raise RuntimeError("DemoService not initialized")
        
        try:
            # 先检查模型是否存在
            available_models = self.manager.get_all_models()
            logger.info(f"Looking for model {model} in available models: {available_models}")
            
            # 构建消息列表
            messages = []
            
            # 如果有system prompt，添加到消息列表开头
            if system_prompt:
                messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
            
            # 添加用户消息
            messages.append(Message(role=MessageRole.USER, content=message))
            
            # 记录请求信息
            logger.info(f"\n{'='*50}\n🤖 AI Request:\n"
                       f"Model: {model}\n"
                       f"Messages:\n{format_messages(messages)}\n{'='*50}")
            
            # 创建聊天请求
            request = ChatCompletionRequest(
                model=model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            # 获取客户端
            client = self.manager.get_client_by_model(model)
            start_time = asyncio.get_event_loop().time()
            response = await client.chat_completion(request)
            process_time = asyncio.get_event_loop().time() - start_time
            
            # 记录响应信息
            logger.info(f"\n{'='*50}\n🤖 AI Response:\n"
                       f"Time: {process_time:.2f}s\n"
                       f"Content: {response.choices[0].message.content}\n"
                       f"Usage: {json.dumps(response.usage.__dict__, indent=2)}\n{'='*50}")
            
            return {
                "success": True,
                "user_message": message,
                "system_prompt": system_prompt,
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
                "system_prompt": system_prompt,
                "model": model
            }

    async def multi_turn_chat(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gemini-2.5-flash",
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """多轮对话接口"""
        if not self._initialized:
            raise RuntimeError("DemoService not initialized")
        
        try:
            # 转换消息格式
            chat_messages = []
            
            # 检查是否已有system消息
            has_system_message = any(msg["role"] == "system" for msg in messages)
            
            # 如果提供了system_prompt且消息列表中没有system消息，添加到开头
            if system_prompt and not has_system_message:
                chat_messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
            
            # 转换其他消息
            for msg in messages:
                if msg["role"] == "user":
                    role = MessageRole.USER
                elif msg["role"] == "assistant":
                    role = MessageRole.ASSISTANT
                elif msg["role"] == "system":
                    role = MessageRole.SYSTEM
                else:
                    continue  # 跳过未知角色
                chat_messages.append(Message(role=role, content=msg["content"]))
            
            # 记录请求信息
            logger.info(f"\n{'='*50}\n🤖 AI Request:\n"
                       f"Model: {model}\n"
                       f"Messages:\n{format_messages(chat_messages)}\n{'='*50}")
            
            # 创建聊天请求
            request = ChatCompletionRequest(
                model=model,
                messages=chat_messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            # 使用 manager 直接获取客户端
            client = self.manager.get_client_by_model(model)
            start_time = asyncio.get_event_loop().time()
            response = await client.chat_completion(request)
            process_time = asyncio.get_event_loop().time() - start_time
            
            # 记录响应信息
            logger.info(f"\n{'='*50}\n🤖 AI Response:\n"
                       f"Time: {process_time:.2f}s\n"
                       f"Content: {response.choices[0].message.content}\n"
                       f"Usage: {json.dumps(response.usage.__dict__, indent=2)}\n{'='*50}")
            
            return {
                "success": True,
                "conversation": messages,
                "system_prompt": system_prompt if not has_system_message else None,
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
                "system_prompt": system_prompt if not has_system_message else None,
                "model": model
            }

    async def stream_chat(
        self, 
        message: str, 
        model: str = "gemini-2.5-flash",
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式聊天接口"""
        if not self._initialized:
            raise RuntimeError("DemoService not initialized")
        
        try:
            # 先检查模型是否存在
            available_models = self.manager.get_all_models()
            logger.info(f"Looking for model {model} in available models: {available_models}")
            
            # 构建消息列表
            messages = []
            
            # 如果有system prompt，添加到消息列表开头
            if system_prompt:
                messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
            
            # 添加用户消息
            messages.append(Message(role=MessageRole.USER, content=message))
            
            # 记录请求信息
            logger.info(f"\n{'='*50}\n🤖 AI Stream Request:\n"
                       f"Model: {model}\n"
                       f"Messages:\n{format_messages(messages)}\n{'='*50}")
            
            # 创建聊天请求
            request = ChatCompletionRequest(
                model=model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )
            
            # 获取客户端并开始流式请求
            client = self.manager.get_client_by_model(model)
            
            # 初始化统计
            total_content = ""
            chunk_count = 0
            start_time = asyncio.get_event_loop().time()
            
            # 发送开始事件
            yield {
                "type": "start",
                "model": model,
                "user_message": message,
                "system_prompt": system_prompt,
                "timestamp": start_time
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
                process_time = asyncio.get_event_loop().time() - start_time
                logger.info(f"\n{'='*50}\n🤖 AI Stream Response:\n"
                           f"Time: {process_time:.2f}s\n"
                           f"Total Chunks: {chunk_count}\n"
                           f"Content: {total_content}\n{'='*50}")
                
                yield {
                    "type": "done",
                    "total_content": total_content,
                    "total_chunks": chunk_count,
                    "model": model,
                    "user_message": message,
                    "system_prompt": system_prompt,
                    "timestamp": asyncio.get_event_loop().time()
                }
            
        except Exception as e:
            logger.error(f"Stream chat failed: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "user_message": message,
                "system_prompt": system_prompt,
                "model": model,
                "timestamp": asyncio.get_event_loop().time()
            }

    async def stream_multi_turn_chat(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gemini-2.5-flash",
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式多轮对话接口"""
        if not self._initialized:
            raise RuntimeError("DemoService not initialized")
        
        try:
            # 转换消息格式
            chat_messages = []
            
            # 检查是否已有system消息
            has_system_message = any(msg["role"] == "system" for msg in messages)
            
            # 如果提供了system_prompt且消息列表中没有system消息，添加到开头
            if system_prompt and not has_system_message:
                chat_messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
            
            # 转换其他消息
            for msg in messages:
                if msg["role"] == "user":
                    role = MessageRole.USER
                elif msg["role"] == "assistant":
                    role = MessageRole.ASSISTANT
                elif msg["role"] == "system":
                    role = MessageRole.SYSTEM
                else:
                    continue  # 跳过未知角色
                chat_messages.append(Message(role=role, content=msg["content"]))
            
            # 记录请求信息
            logger.info(f"\n{'='*50}\n🤖 AI Stream Request:\n"
                       f"Model: {model}\n"
                       f"Messages:\n{format_messages(chat_messages)}\n{'='*50}")
            
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
            start_time = asyncio.get_event_loop().time()
            
            # 发送开始事件
            yield {
                "type": "start",
                "model": model,
                "conversation": messages,
                "system_prompt": system_prompt if not has_system_message else None,
                "timestamp": start_time
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
                process_time = asyncio.get_event_loop().time() - start_time
                logger.info(f"\n{'='*50}\n🤖 AI Stream Response:\n"
                           f"Time: {process_time:.2f}s\n"
                           f"Total Chunks: {chunk_count}\n"
                           f"Content: {total_content}\n{'='*50}")
                
                yield {
                    "type": "done",
                    "total_content": total_content,
                    "total_chunks": chunk_count,
                    "model": model,
                    "conversation": messages,
                    "system_prompt": system_prompt if not has_system_message else None,
                    "timestamp": asyncio.get_event_loop().time()
                }
            
        except Exception as e:
            logger.error(f"Stream multi-turn chat failed: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "conversation": messages,
                "system_prompt": system_prompt if not has_system_message else None,
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