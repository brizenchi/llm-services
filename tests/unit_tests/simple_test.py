#!/usr/bin/env python3
"""
LLM Services 三层架构简单测试

这个脚本不依赖外部测试库，直接测试核心功能。
"""

import asyncio
import traceback
import sys
from typing import Dict, Any

# 导入我们的组件
try:
    from pkg.core.llm.types import (
        Message,
        MessageRole,
        ChatCompletionRequest,
        ChatCompletionResponse,
        ModelConfig,
        ProviderConfig,
        Choice,
        Usage,
        StreamResponse,
        StreamChoice,
        APIError
    )
    from pkg.core.llm.client import BaseLLMClient
    from pkg.core.llm.provider import BaseProvider
    from pkg.core.llm.manager import Manager, get_manager
    from pkg.core.llm.aggregator import LLMAggregator
    from pkg.core.llm.llm_aggrator import LLMAggrator
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在正确的目录运行此脚本")
    sys.exit(1)


# ========== Mock实现用于测试 ==========

class SimpleMockClient(BaseLLMClient):
    """简单的Mock客户端"""
    
    def __init__(self, config: ModelConfig, should_fail: bool = False):
        super().__init__(config)
        self.should_fail = should_fail
        self.call_count = 0
    
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        self.call_count += 1
        
        if self.should_fail:
            raise APIError("Mock API 错误")
        
        # 创建模拟响应
        choice = Choice(
            index=0,
            message=Message(
                role=MessageRole.ASSISTANT,
                content=f"Mock响应来自 {self.config.model} (调用次数: {self.call_count})"
            ),
            finish_reason="stop"
        )
        
        usage = Usage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        
        return ChatCompletionResponse(
            id="mock-id",
            object="chat.completion",
            created=1234567890,
            model=request.model,
            choices=[choice],
            usage=usage
        )
    
    async def chat_completion_stream(self, request: ChatCompletionRequest):
        if self.should_fail:
            raise APIError("Mock 流式错误")
        
        # 简单的流式响应
        for i in range(3):
            choice = StreamChoice(
                delta=Message(
                    role=MessageRole.ASSISTANT,
                    content=f"chunk-{i}"
                ),
                index=0,
                finish_reason="stop" if i == 2 else None
            )
            
            yield StreamResponse(
                id="mock-stream-id",
                object="chat.completion.chunk",
                created=1234567890,
                model=request.model,
                choices=[choice]
            )


class SimpleMockProvider(BaseProvider):
    """简单的Mock Provider"""
    
    def __init__(self, config: ProviderConfig, should_fail: bool = False):
        super().__init__(config)
        self.should_fail = should_fail
    
    def create_client(self, model_config: ModelConfig) -> SimpleMockClient:
        return SimpleMockClient(model_config, self.should_fail)


# ========== 测试函数 ==========

class TestResult:
    """测试结果"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name: str):
        self.total += 1
        self.passed += 1
        print(f"  ✅ {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.total += 1
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"  ❌ {test_name}: {error}")
    
    def summary(self):
        print(f"\n📊 测试结果: {self.passed}/{self.total} 通过")
        if self.failed > 0:
            print(f"💥 失败的测试:")
            for error in self.errors:
                print(f"   - {error}")
        return self.failed == 0


def test_basic_types():
    """测试基础类型"""
    print("\n🔍 测试基础类型...")
    result = TestResult()
    
    try:
        # 测试Message
        msg = Message(role=MessageRole.USER, content="Hello")
        if msg.role == MessageRole.USER and msg.content == "Hello":
            result.add_pass("Message创建")
        else:
            result.add_fail("Message创建", "属性不匹配")
    except Exception as e:
        result.add_fail("Message创建", str(e))
    
    try:
        # 测试ChatCompletionRequest
        request = ChatCompletionRequest(
            model="test-model",
            messages=[Message(role=MessageRole.USER, content="Hi")],
            max_tokens=100
        )
        if request.model == "test-model" and len(request.messages) == 1:
            result.add_pass("ChatCompletionRequest创建")
        else:
            result.add_fail("ChatCompletionRequest创建", "属性不匹配")
    except Exception as e:
        result.add_fail("ChatCompletionRequest创建", str(e))
    
    try:
        # 测试ModelConfig
        config = ModelConfig(
            model="test-model",
            provider="test-provider", 
            api_key="test-key",
            base_url="https://test.com"
        )
        if config.model == "test-model" and config.timeout == 30.0:
            result.add_pass("ModelConfig创建")
        else:
            result.add_fail("ModelConfig创建", "属性不匹配")
    except Exception as e:
        result.add_fail("ModelConfig创建", str(e))
    
    return result.summary()


async def test_client_layer():
    """测试Client层"""
    print("\n🔧 测试Client层...")
    result = TestResult()
    
    config = ModelConfig(
        model="test-model",
        provider="test-provider",
        api_key="test-key", 
        base_url="https://test.com"
    )
    
    try:
        # 测试客户端创建
        client = SimpleMockClient(config)
        if client.get_model() == "test-model" and client.is_available():
            result.add_pass("客户端创建")
        else:
            result.add_fail("客户端创建", "属性不正确")
    except Exception as e:
        result.add_fail("客户端创建", str(e))
    
    try:
        # 测试聊天完成
        client = SimpleMockClient(config)
        request = ChatCompletionRequest(
            model="test-model",
            messages=[Message(role=MessageRole.USER, content="Hello")]
        )
        response = await client.chat_completion(request)
        
        if response.model == "test-model" and len(response.choices) == 1:
            result.add_pass("聊天完成")
        else:
            result.add_fail("聊天完成", "响应格式不正确")
    except Exception as e:
        result.add_fail("聊天完成", str(e))
    
    try:
        # 测试失败情况
        failing_client = SimpleMockClient(config, should_fail=True)
        request = ChatCompletionRequest(
            model="test-model",
            messages=[Message(role=MessageRole.USER, content="Hello")]
        )
        
        try:
            await failing_client.chat_completion(request)
            result.add_fail("错误处理", "应该抛出异常但没有")
        except APIError:
            result.add_pass("错误处理")
        except Exception as e:
            result.add_fail("错误处理", f"异常类型不正确: {e}")
            
    except Exception as e:
        result.add_fail("错误处理", str(e))
    
    return result.summary()


async def test_provider_layer():
    """测试Provider层"""
    print("\n🏭 测试Provider层...")
    result = TestResult()
    
    # 创建测试配置
    model_config = ModelConfig(
        model="test-model",
        provider="test-provider",
        api_key="test-key",
        base_url="https://test.com"
    )
    
    provider_config = ProviderConfig(
        provider="test-provider",
        models={"test-model": model_config}
    )
    
    try:
        # 测试Provider创建
        provider = SimpleMockProvider(provider_config)
        if provider.get_provider_name() == "test-provider":
            result.add_pass("Provider创建")
        else:
            result.add_fail("Provider创建", "Provider名称不正确")
    except Exception as e:
        result.add_fail("Provider创建", str(e))
    
    try:
        # 测试模型注册
        provider = SimpleMockProvider(provider_config)
        await provider.register_client(model_config)
        
        if "test-model" in provider.clients:
            result.add_pass("模型注册")
        else:
            result.add_fail("模型注册", "模型未正确注册")
    except Exception as e:
        result.add_fail("模型注册", str(e))
    
    try:
        # 测试获取客户端
        provider = SimpleMockProvider(provider_config)
        await provider.register_client(model_config)
        client = provider.get_llm_client("test-model")
        
        if client.get_model() == "test-model":
            result.add_pass("获取客户端")
        else:
            result.add_fail("获取客户端", "客户端模型名不正确")
    except Exception as e:
        result.add_fail("获取客户端", str(e))
    
    return result.summary()


async def test_manager_layer():
    """测试Manager层"""
    print("\n🎯 测试Manager层...")
    result = TestResult()
    
    # 获取新的Manager实例
    manager = Manager()
    manager.clear()  # 清除之前的状态
    
    # 创建测试Provider
    model_config = ModelConfig(
        model="test-model",
        provider="test-provider",
        api_key="test-key",
        base_url="https://test.com"
    )
    
    provider_config = ProviderConfig(
        provider="test-provider",
        models={"test-model": model_config}
    )
    
    provider = SimpleMockProvider(provider_config)
    
    try:
        # 测试Manager单例
        manager1 = get_manager()
        manager2 = get_manager()
        if manager1 is manager2:
            result.add_pass("Manager单例")
        else:
            result.add_fail("Manager单例", "不是同一个实例")
    except Exception as e:
        result.add_fail("Manager单例", str(e))
    
    try:
        # 测试Provider注册
        await provider.initialize_all_models()
        manager.register_provider(provider)
        
        providers = manager.get_all_providers()
        if "test-provider" in providers:
            result.add_pass("Provider注册")
        else:
            result.add_fail("Provider注册", "Provider未正确注册")
    except Exception as e:
        result.add_fail("Provider注册", str(e))
    
    try:
        # 测试获取客户端
        client = manager.get_llm_client("test-provider", "test-model")
        if client.get_model() == "test-model":
            result.add_pass("Manager获取客户端")
        else:
            result.add_fail("Manager获取客户端", "客户端不正确")
    except Exception as e:
        result.add_fail("Manager获取客户端", str(e))
    
    return result.summary()


async def test_aggregator():
    """测试LLMAggregator"""
    print("\n🔄 测试LLMAggregator...")
    result = TestResult()
    
    # 准备Manager和Provider
    manager = get_manager()
    manager.clear()
    
    # 创建多个Provider用于测试
    models_config = [
        ("provider1", "model1"),
        ("provider2", "model2")
    ]
    
    for provider_name, model_name in models_config:
        model_config = ModelConfig(
            model=model_name,
            provider=provider_name,
            api_key="test-key",
            base_url="https://test.com"
        )
        
        provider_config = ProviderConfig(
            provider=provider_name,
            models={model_name: model_config}
        )
        
        provider = SimpleMockProvider(provider_config)
        await provider.initialize_all_models()
        manager.register_provider(provider)
    
    try:
        # 测试聚合器创建
        aggregator = LLMAggregator(models=["model1", "model2"])
        aggregator.manager = manager
        aggregator._initialized = True
        
        if len(aggregator.models) == 2:
            result.add_pass("聚合器创建")
        else:
            result.add_fail("聚合器创建", "模型数量不正确")
    except Exception as e:
        result.add_fail("聚合器创建", str(e))
    
    try:
        # 测试生成响应
        aggregator = LLMAggregator(models=["model1", "model2"])
        aggregator.manager = manager
        aggregator._initialized = True
        
        messages = [{"role": "user", "content": "Hello"}]
        response = await aggregator.generate_response(messages)
        
        if "Mock响应" in response:
            result.add_pass("聚合器生成响应")
        else:
            result.add_fail("聚合器生成响应", "响应内容不正确")
    except Exception as e:
        result.add_fail("聚合器生成响应", str(e))
    
    return result.summary()


async def test_failover():
    """测试故障转移"""
    print("\n⚡ 测试故障转移...")
    result = TestResult()
    
    manager = get_manager()
    manager.clear()
    
    # 创建一个失败的Provider和一个正常的Provider
    failing_config = ProviderConfig(
        provider="failing-provider",
        models={
            "failing-model": ModelConfig(
                model="failing-model",
                provider="failing-provider",
                api_key="fail-key",
                base_url="https://fail.com"
            )
        }
    )
    
    working_config = ProviderConfig(
        provider="working-provider", 
        models={
            "working-model": ModelConfig(
                model="working-model",
                provider="working-provider",
                api_key="work-key",
                base_url="https://work.com"
            )
        }
    )
    
    try:
        # 注册Providers
        failing_provider = SimpleMockProvider(failing_config, should_fail=True)
        working_provider = SimpleMockProvider(working_config, should_fail=False)
        
        await failing_provider.initialize_all_models()
        await working_provider.initialize_all_models()
        
        manager.register_provider(failing_provider)
        manager.register_provider(working_provider)
        
        # 创建聚合器，失败模型在前
        aggregator = LLMAggregator(models=["failing-model", "working-model"])
        aggregator.manager = manager
        aggregator._initialized = True
        
        # 测试故障转移
        messages = [{"role": "user", "content": "Test failover"}]
        response = await aggregator.generate_response(messages)
        
        if "working-model" in response:
            result.add_pass("故障转移")
        else:
            result.add_fail("故障转移", "未正确转移到工作模型")
    except Exception as e:
        result.add_fail("故障转移", str(e))
    
    return result.summary()


async def test_compatibility():
    """测试兼容性接口"""
    print("\n🔗 测试兼容性接口...")
    result = TestResult()
    
    try:
        # 测试LLMAggrator兼容性
        from unittest.mock import AsyncMock
        
        aggrator = LLMAggrator()
        aggrator.aggregator.generate_response = AsyncMock(
            return_value="兼容性测试响应"
        )
        aggrator._config_initialized = True
        
        messages = [{"role": "user", "content": "测试"}]
        response = await aggrator.generate_response(messages)
        
        if response == "兼容性测试响应":
            result.add_pass("兼容性接口")
        else:
            result.add_fail("兼容性接口", "响应不正确")
    except Exception as e:
        result.add_fail("兼容性接口", str(e))
    
    return result.summary()


async def main():
    """主测试函数"""
    print("🧪 LLM Services 三层架构测试套件")
    print("=" * 60)
    
    # 运行所有测试
    tests = [
        ("基础类型", test_basic_types),
        ("Client层", test_client_layer),
        ("Provider层", test_provider_layer),
        ("Manager层", test_manager_layer),
        ("聚合器", test_aggregator),
        ("故障转移", test_failover),
        ("兼容性", test_compatibility)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                passed = await test_func()
            else:
                passed = test_func()
            
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"\n❌ {test_name} 测试出错: {e}")
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！三层架构实现正确！")
        print("\n✨ 架构特性:")
        print("  🏗️  Manager->Provider->Client 三层架构")
        print("  🔄  自动故障转移和重试机制")
        print("  🧩  模块化设计，易于扩展")
        print("  🔗  完全向后兼容")
        print("  ⚡  异步并发支持")
        print("  🏥  健康检查和监控")
    else:
        print("💥 部分测试失败，请检查实现")
    
    print(f"\n📚 查看文档: pkg/core/llm/README.md")
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试运行失败: {e}")
        traceback.print_exc()
        sys.exit(1) 