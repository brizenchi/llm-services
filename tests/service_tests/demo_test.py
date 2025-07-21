#!/usr/bin/env python3
"""
Demo测试脚本 - 演示如何使用Demo Service调用Gemini
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pkg.service.demo_service import get_demo_service, initialize_demo_service


async def test_demo_service():
    """测试Demo Service"""
    
    # 加载环境变量
    load_dotenv("deployment/.env")
    
    # 检查API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 错误: 请在 deployment/.env 文件中设置 GEMINI_API_KEY")
        print("   格式: GEMINI_API_KEY=your_api_key_here")
        return
    
    try:
        print("🚀 初始化Demo Service...")
        
        # 配置Gemini
        gemini_config = {
            "provider": "gemini",
            "models": {
                "gemini-2.5-flash": {
                    "api_key": api_key,
                    "base_url": os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
                    "timeout": 300,
                    "max_retries": 3,
                    "max_concurrent_calls": 10
                }
            }
        }
        
        # 初始化服务
        await initialize_demo_service(gemini_config)
        service = await get_demo_service()
        
        print("✅ Demo Service 初始化成功!")
        
        # 测试1: 获取可用模型
        print("\n📋 测试1: 获取可用模型")
        models_result = await service.get_available_models()
        if models_result["success"]:
            print(f"   提供商: {models_result['providers']}")
            print(f"   模型数量: {models_result['total_models']}")
            print(f"   模型列表: {models_result['models']}")
        else:
            print(f"   ❌ 获取模型失败: {models_result['error']}")
        
        # 测试2: 简单聊天
        print("\n💬 测试2: 简单聊天")
        chat_result = await service.simple_chat(
            message="你好，请用中文简短地介绍一下自己。",
            model="gemini-2.0-flash-exp"
        )
        
        if chat_result["success"]:
            print(f"   用户: {chat_result['user_message']}")
            print(f"   模型: {chat_result['model']}")
            print(f"   回复: {chat_result['response']}")
            print(f"   Token使用: {chat_result['usage']}")
        else:
            print(f"   ❌ 聊天失败: {chat_result['error']}")
        
        # 测试3: 多轮对话
        print("\n🔄 测试3: 多轮对话")
        conversation = [
            {"role": "user", "content": "我想学习Python编程"},
            {"role": "assistant", "content": "Python是一门很好的编程语言，适合初学者。你想从哪个方面开始学习？"},
            {"role": "user", "content": "请推荐一些基础的学习资源"}
        ]
        
        multi_turn_result = await service.multi_turn_chat(
            messages=conversation,
            model="gemini-2.0-flash-exp"
        )
        
        if multi_turn_result["success"]:
            print("   对话历史:")
            for msg in conversation:
                print(f"     {msg['role']}: {msg['content']}")
            print(f"   模型回复: {multi_turn_result['response']}")
            print(f"   Token使用: {multi_turn_result['usage']}")
        else:
            print(f"   ❌ 多轮对话失败: {multi_turn_result['error']}")
        
        print("\n🎉 所有测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("=== Demo Service 测试 ===")
    print("此脚本演示如何使用 LLM 架构调用 Gemini 模型")
    print()
    
    # 检查环境文件
    env_file = "deployment/.env"
    if not os.path.exists(env_file):
        print(f"❌ 环境文件不存在: {env_file}")
        print("   请复制 deployment/.env.example 到 deployment/.env 并配置你的API密钥")
        return
    
    # 运行异步测试
    asyncio.run(test_demo_service())


if __name__ == "__main__":
    main() 