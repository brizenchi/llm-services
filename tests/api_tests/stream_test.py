#!/usr/bin/env python3
"""
流式接口测试脚本
测试 Gemini 流式聊天功能
"""

import asyncio
import aiohttp
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class StreamChatTester:
    """流式聊天测试器"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_stream_chat(self, message: str, model: str = "gemini-2.5-flash", token: str = "FHDKdhfukFODIHfo3"):
        """测试流式聊天"""
        print(f"\n🚀 测试流式聊天")
        print(f"消息: {message}")
        print(f"模型: {model}")
        print("-" * 50)
        
        url = f"{self.base_url}/api/v1/demo/chat/stream"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        data = {
            "message": message,
            "model": model
        }
        
        try:
            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    print(f"❌ 请求失败: {response.status}")
                    text = await response.text()
                    print(f"错误信息: {text}")
                    return
                
                print("📡 开始接收流式响应...")
                total_content = ""
                chunk_count = 0
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 去掉 'data: ' 前缀
                        
                        if data_str == '[DONE]':
                            print("\n✅ 流式响应完成")
                            break
                        
                        try:
                            chunk_data = json.loads(data_str)
                            chunk_count += 1
                            
                            if chunk_data.get("type") == "start":
                                print(f"🏁 开始生成回复...")
                            
                            elif chunk_data.get("type") == "content":
                                content = chunk_data.get("content", "")
                                total_content += content
                                print(content, end="", flush=True)
                            
                            elif chunk_data.get("type") == "finish":
                                print(f"\n🎯 生成完成: {chunk_data.get('finish_reason')}")
                                print(f"总块数: {chunk_data.get('total_chunks', 0)}")
                            
                            elif chunk_data.get("type") == "done":
                                print(f"\n✨ 任务完成")
                                print(f"总内容长度: {len(chunk_data.get('total_content', ''))}")
                                print(f"总块数: {chunk_data.get('total_chunks', 0)}")
                            
                            elif chunk_data.get("type") == "error":
                                print(f"\n❌ 错误: {chunk_data.get('message', '未知错误')}")
                                return
                        
                        except json.JSONDecodeError as e:
                            print(f"\n⚠️ JSON解析错误: {e}")
                            print(f"原始数据: {data_str}")
                
                print(f"\n\n📊 测试统计:")
                print(f"  - 接收块数: {chunk_count}")
                print(f"  - 总内容长度: {len(total_content)}")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    async def test_stream_multi_turn_chat(self, messages: list, model: str = "gemini-2.5-flash", token: str = "FHDKdhfukFODIHfo3"):
        """测试流式多轮对话"""
        print(f"\n🚀 测试流式多轮对话")
        print(f"对话历史: {len(messages)} 条消息")
        print(f"模型: {model}")
        print("-" * 50)
        
        # 显示对话历史
        for i, msg in enumerate(messages):
            role_emoji = "👤" if msg["role"] == "user" else "🤖"
            print(f"{role_emoji} {msg['role']}: {msg['content']}")
        
        print("-" * 50)
        
        url = f"{self.base_url}/api/v1/demo/chat/stream/multi-turn"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        data = {
            "messages": messages,
            "model": model
        }
        
        try:
            async with self.session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    print(f"❌ 请求失败: {response.status}")
                    text = await response.text()
                    print(f"错误信息: {text}")
                    return
                
                print("📡 开始接收流式响应...")
                total_content = ""
                chunk_count = 0
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 去掉 'data: ' 前缀
                        
                        if data_str == '[DONE]':
                            print("\n✅ 流式响应完成")
                            break
                        
                        try:
                            chunk_data = json.loads(data_str)
                            chunk_count += 1
                            
                            if chunk_data.get("type") == "start":
                                print(f"🏁 开始生成回复...")
                            
                            elif chunk_data.get("type") == "content":
                                content = chunk_data.get("content", "")
                                total_content += content
                                print(content, end="", flush=True)
                            
                            elif chunk_data.get("type") == "finish":
                                print(f"\n🎯 生成完成: {chunk_data.get('finish_reason')}")
                                print(f"总块数: {chunk_data.get('total_chunks', 0)}")
                            
                            elif chunk_data.get("type") == "done":
                                print(f"\n✨ 任务完成")
                                print(f"总内容长度: {len(chunk_data.get('total_content', ''))}")
                                print(f"总块数: {chunk_data.get('total_chunks', 0)}")
                            
                            elif chunk_data.get("type") == "error":
                                print(f"\n❌ 错误: {chunk_data.get('message', '未知错误')}")
                                return
                        
                        except json.JSONDecodeError as e:
                            print(f"\n⚠️ JSON解析错误: {e}")
                            print(f"原始数据: {data_str}")
                
                print(f"\n\n📊 测试统计:")
                print(f"  - 接收块数: {chunk_count}")
                print(f"  - 总内容长度: {len(total_content)}")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")


async def main():
    """主测试函数"""
    print("🧪 Gemini 流式接口测试")
    print("=" * 60)
    
    async with StreamChatTester() as tester:
        # 测试1: 简单流式聊天
        await tester.test_stream_chat(
            message="请用中文写一首关于编程的短诗",
            model="gemini-2.5-flash"
        )
        
        # 等待一下
        await asyncio.sleep(2)
        
        # 测试2: 流式多轮对话
        conversation = [
            {"role": "user", "content": "你好，我是一名软件工程师"},
            {"role": "assistant", "content": "你好！很高兴认识你。作为软件工程师，你主要使用什么编程语言呢？"},
            {"role": "user", "content": "我主要使用Python和JavaScript。你能给我一些关于代码优化的建议吗？"}
        ]
        
        await tester.test_stream_multi_turn_chat(
            messages=conversation,
            model="gemini-2.5-flash"
        )


if __name__ == "__main__":
    print("请确保服务器正在运行: python app/main.py")
    print("服务器地址: http://127.0.0.1:8000")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}") 