#!/usr/bin/env python3
"""
快速 LLM API 测试脚本

简单快速地测试单个LLM模型调用
"""

import asyncio
import os
import sys
import time
from dotenv import load_dotenv

# 导入LLM组件
try:
    from pkg.core.llm import (
        OpenAIProvider,
        DeepSeekProvider,
        Message,
        MessageRole,
        ChatCompletionRequest
    )
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)


async def quick_test_openai(message: str = "Hello! Please respond in Chinese."):
    """快速测试OpenAI"""
    print("🔍 测试 OpenAI...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-test"):
        print("⚠️  跳过 OpenAI (无有效API密钥)")
        return
    
    try:
        # 创建Provider
        provider = OpenAIProvider.create_simple(
            api_key=api_key,
            model_name="gpt-3.5-turbo",
            base_url=os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        )
        
        await provider.initialize_all_models()
        client = provider.get_llm_client("gpt-3.5-turbo")
        
        # 创建请求
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[Message(role=MessageRole.USER, content=message)],
            max_tokens=100
        )
        
        # 执行请求
        print(f"  📤 发送消息: {message}")
        start_time = time.time()
        
        response = await client.chat_completion(request)
        
        duration = time.time() - start_time
        content = response.choices[0].message.content if response.choices else "无响应"
        tokens = response.usage.total_tokens if response.usage else 0
        
        print(f"  ✅ OpenAI 响应 ({duration:.2f}s, {tokens} tokens):")
        print(f"     {content}")
        
        # await provider.close_all()  # 暂时注释掉，避免方法不存在的错误
        
    except Exception as e:
        print(f"  ❌ OpenAI 失败: {e}")


async def quick_test_deepseek(message: str = "Hello! Please respond in Chinese."):
    """快速测试DeepSeek"""
    print("\n🔍 测试 DeepSeek...")
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or api_key.startswith("test-"):
        print("⚠️  跳过 DeepSeek (无有效API密钥)")
        return
    
    try:
        # 创建Provider
        provider = DeepSeekProvider.create_simple(
            api_key=api_key,
            model_name="deepseek-chat",
            base_url=os.getenv("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com/v1")
        )
        
        await provider.initialize_all_models()
        client = provider.get_llm_client("deepseek-chat")
        
        # 创建请求
        request = ChatCompletionRequest(
            model="deepseek-chat",
            messages=[Message(role=MessageRole.USER, content=message)],
            max_tokens=100
        )
        
        # 执行请求
        print(f"  📤 发送消息: {message}")
        start_time = time.time()
        
        response = await client.chat_completion(request)
        
        duration = time.time() - start_time
        content = response.choices[0].message.content if response.choices else "无响应"
        tokens = response.usage.total_tokens if response.usage else 0
        
        print(f"  ✅ DeepSeek 响应 ({duration:.2f}s, {tokens} tokens):")
        print(f"     {content}")
        
        # await provider.close_all()  # 暂时注释掉，避免方法不存在的错误
        
    except Exception as e:
        print(f"  ❌ DeepSeek 失败: {e}")


async def main():
    """主函数"""
    print("⚡ LLM Services 快速 API 测试")
    print("=" * 50)
    
    # 加载环境变量
    env_file = "deployment/.env"
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"📋 已加载配置: {env_file}")
    else:
        print(f"⚠️  配置文件不存在: {env_file}")
        print("💡 请创建配置文件并添加API密钥")
        return
    
    # 自定义测试消息（如果需要）
    test_message = sys.argv[1] if len(sys.argv) > 1 else "你好！请用中文简单介绍一下你自己。"
    print(f"💬 测试消息: {test_message}")
    print()
    
    # 测试各个Provider
    await quick_test_openai(test_message)
    await quick_test_deepseek(test_message)
    
    print("\n🎉 快速测试完成！")
    print("💡 提示: 使用 'python3 quick_test.py \"你的消息\"' 自定义测试消息")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试失败: {e}") 