#!/usr/bin/env python3
"""
Gemini API 测试脚本

专门测试Google Gemini API的调用
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入LLM组件
try:
    from pkg.core.llm import (
        GeminiProvider,
        Message,
        MessageRole,
        ChatCompletionRequest
    )
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)


async def test_gemini_basic():
    """测试Gemini基础功能"""
    print("🔍 测试 Gemini 基础功能...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("your-"):
        print("⚠️  跳过 Gemini (无有效API密钥)")
        print("💡 请在 deployment/.env 中设置 GEMINI_API_KEY")
        return False
    
    try:
        # 创建Provider
        provider = GeminiProvider.create_simple(
            api_key=api_key,
            model_name="gemini-2.0-flash-exp",
            base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
        )
        
        await provider.initialize_all_models()
        client = provider.get_llm_client("gemini-2.0-flash-exp")
        
        # 创建请求
        request = ChatCompletionRequest(
            model="gemini-2.0-flash-exp",
            messages=[
                Message(role=MessageRole.SYSTEM, content="你是一个有用的AI助手，请用中文回答。"),
                Message(role=MessageRole.USER, content="请简单介绍一下Google Gemini模型。")
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        # 执行请求
        print(f"  📤 发送消息: 请简单介绍一下Google Gemini模型")
        start_time = time.time()
        
        response = await client.chat_completion(request)
        
        duration = time.time() - start_time
        content = response.choices[0].message.content if response.choices else "无响应"
        tokens = response.usage.total_tokens if response.usage else 0
        
        print(f"  ✅ Gemini 响应 ({duration:.2f}s, {tokens} tokens):")
        print(f"     {content}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Gemini 测试失败: {e}")
        return False


async def test_gemini_models():
    """测试不同的Gemini模型"""
    print("\n🔍 测试不同的 Gemini 模型...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("your-"):
        print("⚠️  跳过模型测试 (无有效API密钥)")
        return False
    
    # 不同的Gemini模型
    models = [
        "gemini-2.5-flash",
    ]
    
    success_count = 0
    
    for model_name in models:
        try:
            print(f"\n  📋 测试模型: {model_name}")
            
            provider = GeminiProvider.create_simple(
                api_key=api_key,
                model_name=model_name
            )
            
            await provider.initialize_all_models()
            client = provider.get_llm_client(model_name)
            
            request = ChatCompletionRequest(
                model=model_name,
                messages=[
                    Message(role=MessageRole.USER, content="Hello! Please respond with 'Model test successful' in Chinese.")
                ],
                max_tokens=50
            )
            
            start_time = time.time()
            response = await client.chat_completion(request)
            duration = time.time() - start_time
            
            if response.choices:
                content = response.choices[0].message.content
                print(f"    ✅ {model_name}: {duration:.2f}s - {content[:50]}...")
                success_count += 1
            else:
                print(f"    ❌ {model_name}: 无响应")
                
        except Exception as e:
            print(f"    ❌ {model_name}: {str(e)[:100]}...")
    
    print(f"\n📊 模型测试结果: {success_count}/{len(models)} 成功")
    return success_count > 0


async def test_gemini_stream():
    """测试Gemini流式响应"""
    print("\n🌊 测试 Gemini 流式响应...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("your-"):
        print("⚠️  跳过流式测试 (无有效API密钥)")
        return False
    
    try:
        provider = GeminiProvider.create_simple(
            api_key=api_key,
            model_name="gemini-2.0-flash"
        )
        
        await provider.initialize_all_models()
        client = provider.get_llm_client("gemini-2.0-flash-exp")
        
        request = ChatCompletionRequest(
            model="gemini-2.0-flash-exp",
            messages=[
                Message(role=MessageRole.USER, content="请用中文写一首关于春天的短诗，每行单独输出。")
            ],
            max_tokens=200
        )
        
        print(f"  📤 发送流式请求...")
        print(f"  📝 流式响应:")
        
        chunk_count = 0
        start_time = time.time()
        
        async for chunk in client.chat_completion_stream(request):
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(f"     {content}", end="", flush=True)
                chunk_count += 1
        
        duration = time.time() - start_time
        print(f"\n  ✅ 流式测试完成: {chunk_count} 个chunks, {duration:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 流式测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("🧪 Google Gemini API 测试")
    print("=" * 50)
    
    # 加载环境变量
    env_file = project_root / "deployment" / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"📋 已加载配置: {env_file}")
    else:
        print(f"⚠️  配置文件不存在: {env_file}")
        print("💡 请创建配置文件并添加 GEMINI_API_KEY")
        return
    
    # 检查API密钥
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 缺少 GEMINI_API_KEY 环境变量")
        print("💡 请在 deployment/.env 中添加:")
        print("   GEMINI_API_KEY=your-gemini-api-key-here")
        return
    
    if api_key.startswith("your-"):
        print("❌ 请替换为真实的 Gemini API 密钥")
        return
    
    print(f"🔑 使用API密钥: {api_key[:8]}...{api_key[-4:]}")
    print()
    
    # 运行测试
    results = []
    
    # 基础功能测试
    results.append(("基础功能", await test_gemini_basic()))
    
    # 多模型测试
    results.append(("模型测试", await test_gemini_models()))
    
    # 流式测试
    results.append(("流式响应", await test_gemini_stream()))
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"\n🎉 所有测试通过！({success_count}/{total_count})")
    else:
        print(f"\n💥 部分测试失败：{success_count}/{total_count}")
        
    print("\n💡 获取Gemini API密钥: https://ai.google.dev/")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试失败: {e}")
        import traceback
        traceback.print_exc() 