import asyncio
import logging
from typing import List, Dict, Any, Optional
from .manager import get_manager, Manager
from .types import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Message,
    MessageRole,
    ModelNotFoundError,
    ProviderNotFoundError,
    APIError
)
from .providers import OpenAIProvider, DeepSeekProvider

logger = logging.getLogger(__name__)


class LLMAggregator:
    """
    LLM聚合器 - 使用三层架构管理多个LLM模型
    
    支持多Provider、多模型的灵活调用，具有自动故障转移功能
    """
    
    def __init__(self, models: Optional[List[str]] = None):
        """
        初始化LLM聚合器
        
        Args:
            models: 模型列表，如果为None则使用已注册的所有模型
        """
        self.manager: Manager = get_manager()
        self.models = models or []
        self._initialized = False
    
    async def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        初始化聚合器，注册Provider和模型
        
        Args:
            config: 配置字典，包含Provider和模型配置
        """
        if self._initialized:
            logger.info("LLMAggregator already initialized")
            return
        
        if config:
            await self._register_providers_from_config(config)
        
        # 如果没有指定模型列表，获取所有可用模型
        if not self.models:
            all_models = self.manager.get_all_models()
            self.models = []
            for provider_models in all_models.values():
                self.models.extend(provider_models)
        
        self._initialized = True
        logger.info(f"LLMAggregator initialized with models: {self.models}")
    
    async def _register_providers_from_config(self, config: Dict[str, Any]) -> None:
        """
        从配置注册Provider
        
        Args:
            config: 配置字典
        """
        for provider_name, provider_config in config.items():
            try:
                if provider_name.lower() == "openai":
                    provider = OpenAIProvider.create_from_config(
                        provider_name=provider_name,
                        models_config=provider_config.get("models", {})
                    )
                elif provider_name.lower() == "deepseek":
                    provider = DeepSeekProvider.create_from_config(
                        provider_name=provider_name,
                        models_config=provider_config.get("models", {})
                    )
                else:
                    logger.warning(f"Unknown provider type: {provider_name}")
                    continue
                
                # 初始化所有模型
                await provider.initialize_all_models()
                
                # 注册到Manager
                self.manager.register_provider(provider)
                
                logger.info(f"Successfully registered provider: {provider_name}")
                
            except Exception as e:
                logger.error(f"Failed to register provider {provider_name}: {e}")
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_retries: int = 3
    ) -> str:
        """
        使用可用模型生成响应，支持自动故障转移
        
        Args:
            messages: 消息列表
            max_retries: 每个模型的最大重试次数
            
        Returns:
            生成的响应文本
            
        Raises:
            RuntimeError: 所有模型都失败时抛出
        """
        if not self._initialized:
            raise RuntimeError("LLMAggregator not initialized. Call initialize() first.")
        
        # 转换消息格式
        llm_messages = [
            Message(
                role=MessageRole(msg["role"]),
                content=msg["content"]
            )
            for msg in messages
        ]
        
        last_error = None
        
        for model_name in self.models:
            try:
                logger.info(f"Attempting to generate response using {model_name}")
                
                # 获取客户端
                client = self.manager.get_client_by_model(model_name)
                
                if not client.is_available():
                    logger.warning(f"Model {model_name} is not available, skipping")
                    continue
                
                # 创建请求
                request = ChatCompletionRequest(
                    model=model_name,
                    messages=llm_messages
                )
                
                # 执行请求
                response = await client.chat_completion(request)
                
                if response.choices and response.choices[0].message:
                    result = response.choices[0].message.content
                    logger.info(f"Successfully generated response using {model_name}")
                    return result
                    
            except (ModelNotFoundError, ProviderNotFoundError) as e:
                logger.warning(f"Model {model_name} not found: {e}")
                continue
                
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to generate response using {model_name}: {e}")
                continue
        
        error_msg = f"All models failed to generate response. Last error: {last_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    async def generate_summary(
        self, 
        passage: Dict[str, Any], 
        count: int
    ) -> str:
        """
        生成文章摘要
        
        Args:
            passage: 文章内容字典，包含title、description、content等字段
            count: 摘要字数限制
            
        Returns:
            生成的摘要
        """
        system_prompt = (
            f"You are a keyword extraction expert, skilled at distilling article key points. "
            f"Please keep the summary within {count} characters."
        )
        
        user_prompt = f"""
        Summarize the article in one word within {count} characters. Extract only facts and data, 
        remove redundant words, and try to explain clearly in one sentence if possible.

        Article Title: {passage.get('title', '')}
        Content: {passage.get('description', '')}. {passage.get('content', '')}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.generate_response(messages)
    
    async def health_check(self) -> Dict[str, Dict[str, bool]]:
        """
        检查所有模型的健康状态
        
        Returns:
            Provider到模型健康状态的映射
        """
        return await self.manager.health_check_all()
    
    def get_available_models(self) -> List[str]:
        """
        获取当前可用的模型列表
        
        Returns:
            可用模型名称列表
        """
        if not self._initialized:
            return []
        
        available_models = []
        for model_name in self.models:
            try:
                client = self.manager.get_client_by_model(model_name)
                if client.is_available():
                    available_models.append(model_name)
            except Exception:
                continue
        
        return available_models
    
    async def close(self) -> None:
        """关闭所有连接"""
        await self.manager.close_all()


# 示例用法
async def main():
    """示例使用方法"""
    # 创建聚合器
    aggregator = LLMAggregator()
    
    # 配置示例
    config = {
        "openai": {
            "models": {
                "gpt-3.5-turbo": {
                    "api_key": "your-openai-api-key",
                    "base_url": "https://api.openai.com/v1"
                }
            }
        },
        "deepseek": {
            "models": {
                "deepseek-chat": {
                    "api_key": "your-deepseek-api-key",
                    "base_url": "https://api.deepseek.com/v1"
                }
            }
        }
    }
    
    # 初始化
    await aggregator.initialize(config)
    
    # 使用
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, who are you?"}
    ]
    
    try:
        response = await aggregator.generate_response(messages)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await aggregator.close()


if __name__ == '__main__':
    asyncio.run(main()) 