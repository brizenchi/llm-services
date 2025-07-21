# LLM Services - Three-Layer Architecture

基于Go版本的三层架构设计，在Python中实现了Manager、Provider、Client三层架构的LLM服务管理系统。

## 架构设计

### 三层架构概述

```
Manager (管理层)
├── Provider (提供商层)
│   ├── OpenAI Provider
│   │   ├── gpt-3.5-turbo (Client)
│   │   ├── gpt-4 (Client)
│   │   └── ...
│   ├── DeepSeek Provider
│   │   ├── deepseek-chat (Client)
│   │   ├── deepseek-coder (Client)
│   │   └── ...
│   └── 其他Provider...
```

### 各层职责

#### 1. Manager层 (`manager.py`)
- **职责**: 全局管理所有Provider，提供统一的访问入口
- **功能**:
  - Provider注册和管理
  - 模型查找和客户端获取
  - 健康检查和状态监控
  - 资源清理和连接管理

#### 2. Provider层 (`provider.py`)
- **职责**: 管理特定服务商的多个模型
- **功能**:
  - 模型客户端创建和注册
  - 服务商特定的配置管理
  - 模型可用性检查
  - 批量初始化和健康检查

#### 3. Client层 (`client.py`)
- **职责**: 具体模型的API调用实现
- **功能**:
  - HTTP请求处理
  - 重试和错误处理
  - 流式和非流式响应
  - 连接池管理

## 使用方法

### 1. 基础使用

```python
import asyncio
from pkg.core.llm import get_manager, OpenAIProvider, DeepSeekProvider

async def basic_usage():
    # 获取全局Manager
    manager = get_manager()
    
    # 创建并注册Provider
    openai_provider = OpenAIProvider.create_simple(
        api_key="your-openai-key",
        model_name="gpt-3.5-turbo"
    )
    await openai_provider.initialize_all_models()
    manager.register_provider(openai_provider)
    
    # 获取客户端并使用
    client = manager.get_llm_client("openai", "gpt-3.5-turbo")
    
    from pkg.core.llm.types import ChatCompletionRequest, Message, MessageRole
    request = ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            Message(role=MessageRole.USER, content="Hello!")
        ]
    )
    
    response = await client.chat_completion(request)
    print(response.choices[0].message.content)
    
    await manager.close_all()

asyncio.run(basic_usage())
```

### 2. 使用LLMAggregator

```python
import asyncio
from pkg.core.llm import LLMAggregator

async def aggregator_usage():
    # 创建聚合器
    aggregator = LLMAggregator()
    
    # 配置多个Provider
    config = {
        "openai": {
            "models": {
                "gpt-3.5-turbo": {
                    "api_key": "your-openai-key",
                    "base_url": "https://api.openai.com/v1"
                },
                "gpt-4": {
                    "api_key": "your-openai-key",
                    "base_url": "https://api.openai.com/v1"
                }
            }
        },
        "deepseek": {
            "models": {
                "deepseek-chat": {
                    "api_key": "your-deepseek-key",
                    "base_url": "https://api.deepseek.com/v1"
                }
            }
        }
    }
    
    # 初始化
    await aggregator.initialize(config)
    
    # 使用 - 自动故障转移
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, who are you?"}
    ]
    
    response = await aggregator.generate_response(messages)
    print(response)
    
    # 健康检查
    health = await aggregator.health_check()
    print(f"Health status: {health}")
    
    await aggregator.close()

asyncio.run(aggregator_usage())
```

### 3. 兼容原有接口

```python
import asyncio
from pkg.core.llm.llm_aggrator import LLMAggrator

async def compatibility_usage():
    # 使用原有的接口，但底层使用新架构
    llm_aggrator = LLMAggrator()
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ]
    
    response = await llm_aggrator.generate_response(messages)
    print(response)
    
    await llm_aggrator.close()

asyncio.run(compatibility_usage())
```

## 配置格式

### Provider配置

```python
config = {
    "provider_name": {
        "models": {
            "model_name": {
                "api_key": "your-api-key",
                "base_url": "https://api.example.com/v1",
                "timeout": 30.0,
                "max_retries": 3,
                "max_concurrent_calls": 10
            }
        }
    }
}
```

### 从Settings配置转换

```python
# 原有settings格式
settings.LLM_MODEL = {
    "gpt-3.5-turbo": {
        "api_key": "sk-...",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo"
    }
}

# 自动转换到新格式
aggregator = LLMAggregator()
await aggregator.initialize_from_settings(settings)
```

## 核心组件

### 数据类型 (`types.py`)

- `Message`: 聊天消息
- `ChatCompletionRequest`: 聊天完成请求
- `ChatCompletionResponse`: 聊天完成响应
- `StreamResponse`: 流式响应
- `ModelConfig`: 模型配置
- `ProviderConfig`: Provider配置

### 异常类型

- `LLMError`: LLM相关错误基类
- `ModelNotFoundError`: 模型未找到
- `ProviderNotFoundError`: Provider未找到
- `APIError`: API调用错误

## 扩展新Provider

```python
from pkg.core.llm.provider import BaseProvider
from pkg.core.llm.client import BaseLLMClient

class MyCustomClient(BaseLLMClient):
    async def chat_completion(self, request):
        # 实现具体的API调用
        pass
    
    async def chat_completion_stream(self, request):
        # 实现流式API调用
        pass

class MyCustomProvider(BaseProvider):
    def create_client(self, model_config):
        return MyCustomClient(model_config)
```

## 优势

1. **清晰的职责分离**: 每层都有明确的职责
2. **易于扩展**: 新增Provider和模型非常简单
3. **故障转移**: 自动在模型间切换
4. **资源管理**: 统一的连接池和资源清理
5. **健康监控**: 实时的模型状态检查
6. **向后兼容**: 保持原有接口不变

## 性能特性

- 异步IO操作
- 连接池复用
- 自动重试机制
- 并发限制控制
- 优雅的资源清理 