# 新的三层架构实现示例
# 使用 Manager -> Provider -> Client 架构
import asyncio
import logging
from typing import List, Dict, Any

# 导入新的三层架构组件
from .aggregator import LLMAggregator
from .manager import get_manager
from .providers import OpenAIProvider, DeepSeekProvider
from .types import Message, MessageRole, ChatCompletionRequest

logger = logging.getLogger(__name__)

# 保持与原有接口的兼容性
class LLMAggrator:  # 保持原有的类名以兼容现有代码
    """
    LLM聚合器 - 基于新的三层架构实现
    
    这是对原有LLMAggrator类的升级版本，使用了Manager->Provider->Client三层架构：
    - Manager: 管理所有Provider
    - Provider: 管理特定服务商（如OpenAI、DeepSeek）的多个模型
    - Client: 具体模型的客户端实现
    
    优势：
    1. 更好的代码组织和扩展性
    2. 支持多Provider多模型的统一管理
    3. 自动故障转移和重试机制
    4. 健康检查和状态管理
    """
    
    def __init__(self, models: List[str] = None):
        """
        初始化LLM聚合器
        
        Args:
            models: 模型列表，如果为None则使用所有可用模型
        """
        self.aggregator = LLMAggregator(models)
        self._config_initialized = False
        logger.info("LLMAggrator initialized with new three-layer architecture")
    
    async def initialize_from_settings(self, settings):
        """
        从settings配置初始化
        
        Args:
            settings: 配置对象，包含LLM_MODEL配置
        """
        if self._config_initialized:
            return
        
        # 转换settings配置到新的格式
        config = {}
        
        if hasattr(settings, 'LLM_MODEL') and settings.LLM_MODEL:
            for model_name, model_config in settings.LLM_MODEL.items():
                # 根据模型名称推断Provider
                if 'gpt' in model_name.lower() or 'openai' in model_name.lower():
                    provider_name = 'openai'
                elif 'deepseek' in model_name.lower():
                    provider_name = 'deepseek'
                else:
                    # 默认使用openai
                    provider_name = 'openai'
                
                if provider_name not in config:
                    config[provider_name] = {"models": {}}
                
                config[provider_name]["models"][model_name] = {
                    "api_key": model_config.get("api_key", ""),
                    "base_url": model_config.get("base_url", ""),
                    "model": model_config.get("model", model_name),
                    "timeout": model_config.get("timeout", 30.0),
                    "max_retries": model_config.get("max_retries", 3),
                    "max_concurrent_calls": model_config.get("max_concurrent_calls", 10)
                }
        
        await self.aggregator.initialize(config)
        self._config_initialized = True
        logger.info("LLMAggrator initialized from settings")
    
    async def generate_response(self, messages: List[Dict[str, str]], max_retries: int = 3) -> str:
        """
        生成响应（兼容原有接口）
        
        Args:
            messages: 消息列表
            max_retries: 最大重试次数
            
        Returns:
            生成的响应
        """
        if not self._config_initialized:
            # 如果没有初始化，尝试使用默认配置
            logger.warning("LLMAggrator not initialized, using default config")
            await self._initialize_default()
        
        return await self.aggregator.generate_response(messages, max_retries)
    
    async def generate_summary(self, passage: Dict[str, Any], count: int) -> str:
        """
        生成摘要（兼容原有接口）
        
        Args:
            passage: 文章内容
            count: 摘要字数
            
        Returns:
            生成的摘要
        """
        if not self._config_initialized:
            await self._initialize_default()
        
        return await self.aggregator.generate_summary(passage, count)
    
    async def _initialize_default(self):
        """初始化默认配置"""
        default_config = {
            "openai": {
                "models": {
                    "gpt-3.5-turbo": {
                        "api_key": "your-api-key-here",
                        "base_url": "https://api.openai.com/v1"
                    }
                }
            }
        }
        await self.aggregator.initialize(default_config)
        self._config_initialized = True
    
    async def health_check(self) -> Dict[str, Dict[str, bool]]:
        """健康检查"""
        return await self.aggregator.health_check()
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return self.aggregator.get_available_models()
    
    async def close(self):
        """关闭连接"""
        await self.aggregator.close()


# 新架构的直接使用示例
async def example_new_architecture():
    """演示新三层架构的使用方法"""
    
    # 1. 获取全局Manager
    manager = get_manager()
    
    # 2. 创建和注册Provider
    openai_provider = OpenAIProvider.create_simple(
        api_key="your-openai-key",
        model_name="gpt-3.5-turbo"
    )
    await openai_provider.initialize_all_models()
    manager.register_provider(openai_provider)
    
    deepseek_provider = DeepSeekProvider.create_simple(
        api_key="your-deepseek-key", 
        model_name="deepseek-chat"
    )
    await deepseek_provider.initialize_all_models()
    manager.register_provider(deepseek_provider)
    
    # 3. 直接使用Manager获取客户端
    try:
        # 方式1: 指定Provider和模型
        client1 = manager.get_llm_client("openai", "gpt-3.5-turbo")
        
        # 方式2: 直接根据模型名查找
        client2 = manager.get_client_by_model("deepseek-chat")
        
        # 4. 使用客户端
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[
                Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
                Message(role=MessageRole.USER, content="Hello!")
            ]
        )
        
        response = await client1.chat_completion(request)
        print(f"Response: {response.choices[0].message.content}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
    
    finally:
        # 5. 清理资源
        await manager.close_all()


# 保持原有的main函数以便兼容
async def main():
    """示例用法 - 兼容原有接口"""
    llm_aggrator = LLMAggrator()  # 使用新架构实现
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "who are you."}
    ]
    
    try:
        response = await llm_aggrator.generate_response(messages)
        print(response)
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await llm_aggrator.close()


if __name__ == '__main__':
    # 可以运行原有接口示例或新架构示例
    print("Running compatibility example...")
    asyncio.run(main())
    
    print("\nRunning new architecture example...")
    asyncio.run(example_new_architecture())