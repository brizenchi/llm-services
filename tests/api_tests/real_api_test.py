#!/usr/bin/env python3
"""
真实 LLM API 测试脚本

根据 deployment/.env 配置文件，测试真实的 LLM API 调用
"""

import asyncio
import os
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, List
import time

# 加载环境变量
from dotenv import load_dotenv

# 导入LLM组件
try:
    from pkg.core.llm import (
        get_manager,
        OpenAIProvider,
        DeepSeekProvider,
        ModelConfig,
        ProviderConfig,
        Message,
        MessageRole,
        ChatCompletionRequest,
        LLMAggregator
    )
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在正确的目录运行此脚本")
    sys.exit(1)


class RealAPITester:
    """真实API测试器"""
    
    def __init__(self, env_file: str = "deployment/.env"):
        self.env_file = env_file
        self.manager = get_manager()
        self.providers_config = {}
        self.test_results = []
        
    def load_config(self):
        """加载环境配置"""
        print(f"📋 加载配置文件: {self.env_file}")
        
        if not os.path.exists(self.env_file):
            print(f"❌ 配置文件不存在: {self.env_file}")
            return False
            
        load_dotenv(self.env_file)
        
        # 检查必要的配置
        configs = {
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "base_url": os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1"),
                "timeout": float(os.getenv("OPENAI_TIMEOUT", "30")),
                "max_retries": int(os.getenv("OPENAI_MAX_RETRIES", "3"))
            },
            "deepseek": {
                "api_key": os.getenv("DEEPSEEK_API_KEY"),
                "base_url": os.getenv("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com/v1"),
                "timeout": float(os.getenv("DEEPSEEK_TIMEOUT", "30")),
                "max_retries": int(os.getenv("DEEPSEEK_MAX_RETRIES", "3"))
            }
        }
        
        # 只保留有API Key的配置
        for provider_name, config in configs.items():
            if config["api_key"] and config["api_key"].strip():
                if not config["api_key"].startswith("sk-test") and not config["api_key"].startswith("test-"):
                    self.providers_config[provider_name] = config
                    print(f"✅ 发现 {provider_name.upper()} 配置")
                else:
                    print(f"⚠️  跳过 {provider_name.upper()} (测试密钥)")
            else:
                print(f"⚠️  跳过 {provider_name.upper()} (无API密钥)")
        
        if not self.providers_config:
            print("❌ 没有发现有效的API配置")
            print("💡 请在 deployment/.env 中配置真实的API密钥")
            return False
            
        return True
    
    async def setup_providers(self):
        """设置真实的Provider"""
        print("\n🔧 设置 LLM Providers...")
        
        self.manager.clear()
        
        for provider_name, config in self.providers_config.items():
            try:
                if provider_name == "openai":
                    # 测试常见的OpenAI模型
                    models = ["gpt-3.5-turbo", "gpt-4o"]
                    provider = None
                    
                    for model in models:
                        try:
                            provider = OpenAIProvider.create_simple(
                                api_key=config["api_key"],
                                model_name=model,
                                base_url=config["base_url"],
                                # timeout=config["timeout"],
                                # max_retries=config["max_retries"]
                            )
                            await provider.initialize_all_models()
                            self.manager.register_provider(provider)
                            print(f"  ✅ OpenAI {model}")
                            break
                        except Exception as e:
                            print(f"  ⚠️  OpenAI {model} 不可用: {str(e)[:1000]}...")
                            continue
                    
                elif provider_name == "deepseek":
                    # 测试DeepSeek模型
                    models = ["deepseek-chat"]
                    
                    for model in models:
                        try:
                            provider = DeepSeekProvider.create_simple(
                                api_key=config["api_key"],
                                model_name=model,
                                base_url=config["base_url"],
                                # timeout=config["timeout"],
                                # max_retries=config["max_retries"]
                            )
                            await provider.initialize_all_models()
                            self.manager.register_provider(provider)
                            print(f"  ✅ DeepSeek {model}")
                            break
                        except Exception as e:
                            print(f"  ⚠️  DeepSeek {model} 不可用: {str(e)[:1000]}...")
                            continue
                            
            except Exception as e:
                print(f"  ❌ {provider_name.upper()} 设置失败: {e}")
        
        # 检查是否有成功注册的Provider
        all_providers = self.manager.get_all_providers()
        if not all_providers:
            print("❌ 没有成功注册任何Provider")
            return False
            
        print(f"✅ 成功注册 {len(all_providers)} 个Provider")
        return True
    
    async def test_single_model(self, provider_name: str, model_name: str, test_message: str = "Hello! Please respond in Chinese."):
        """测试单个模型"""
        print(f"\n🔍 测试 {provider_name}/{model_name}")
        
        try:
            # 获取客户端
            client = self.manager.get_llm_client(provider_name, model_name)
            
            # 创建请求
            request = ChatCompletionRequest(
                model=model_name,
                messages=[
                    Message(role=MessageRole.USER, content=test_message)
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            # 记录开始时间
            start_time = time.time()
            
            # 执行请求
            response = await client.chat_completion(request)
            
            # 计算耗时
            duration = time.time() - start_time
            
            # 提取响应内容
            content = response.choices[0].message.content if response.choices else "无响应"
            
            result = {
                "provider": provider_name,
                "model": model_name,
                "status": "success",
                "duration": duration,
                "content": content,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
            print(f"  ✅ 响应 ({duration:.2f}s, {result['tokens_used']} tokens):")
            print(f"     {content[:100]}{'...' if len(content) > 100 else ''}")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            error_msg = str(e)
            result = {
                "provider": provider_name,
                "model": model_name,
                "status": "error",
                "error": error_msg
            }
            
            print(f"  ❌ 失败: {error_msg}")
            self.test_results.append(result)
            return result
    
    async def test_all_models(self):
        """测试所有可用模型"""
        print("\n🚀 开始测试所有模型...")
        
        all_provider_names = self.manager.get_all_providers()
        test_messages = [
            "Hello! Please introduce yourself in Chinese.",
            "用中文写一首关于春天的短诗。",
            "What is 2+2? Please explain in Chinese."
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n📝 测试消息 {i}: {message}")
            
            for provider_name in all_provider_names:
                try:
                    provider = self.manager.get_provider(provider_name)
                    for model_name in provider.clients.keys():
                        await self.test_single_model(provider_name, model_name, message)
                        # 短暂延迟避免API限流
                        await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  ❌ 跳过 Provider {provider_name}: {e}")
    
    async def test_aggregator(self):
        """测试聚合器功能"""
        print("\n🔄 测试 LLM 聚合器...")
        
        try:
            # 获取所有可用模型
            available_models = []
            for provider_name in self.manager.get_all_providers():
                try:
                    provider = self.manager.get_provider(provider_name)
                    for model_name in provider.clients.keys():
                        available_models.append(model_name)
                except Exception as e:
                    print(f"  ⚠️  跳过 Provider {provider_name}: {e}")
                    continue
            
            if not available_models:
                print("❌ 没有可用模型进行聚合测试")
                return
            
            # 创建聚合器
            aggregator = LLMAggregator(models=available_models[:2])  # 最多使用2个模型
            aggregator.manager = self.manager
            aggregator._initialized = True
            
            # 测试生成响应
            messages = [
                {"role": "system", "content": "你是一个有用的AI助手，请用中文回答。"},
                {"role": "user", "content": "请简单介绍一下人工智能的发展历程。"}
            ]
            
            start_time = time.time()
            response = await aggregator.generate_response(messages)
            duration = time.time() - start_time
            
            print(f"  ✅ 聚合器响应 ({duration:.2f}s):")
            print(f"     {response[:200]}{'...' if len(response) > 200 else ''}")
            
            # 测试健康检查
            health = await aggregator.health_check()
            print(f"  ✅ 健康检查: {health}")
            
            await aggregator.close()
            
        except Exception as e:
            print(f"  ❌ 聚合器测试失败: {e}")
            traceback.print_exc()
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 测试结果总结")
        print("=" * 60)
        
        if not self.test_results:
            print("❌ 没有测试结果")
            return
        
        success_count = sum(1 for r in self.test_results if r["status"] == "success")
        total_count = len(self.test_results)
        
        print(f"总测试数: {total_count}")
        print(f"成功: {success_count}")
        print(f"失败: {total_count - success_count}")
        print(f"成功率: {success_count/total_count*100:.1f}%")
        
        print("\n📈 详细结果:")
        
        # 按Provider分组
        by_provider = {}
        for result in self.test_results:
            provider = result["provider"]
            if provider not in by_provider:
                by_provider[provider] = []
            by_provider[provider].append(result)
        
        for provider_name, results in by_provider.items():
            print(f"\n🔹 {provider_name.upper()}:")
            for result in results:
                status_icon = "✅" if result["status"] == "success" else "❌"
                model = result["model"]
                
                if result["status"] == "success":
                    duration = result.get("duration", 0)
                    tokens = result.get("tokens_used", 0)
                    print(f"  {status_icon} {model}: {duration:.2f}s, {tokens} tokens")
                else:
                    error = result.get("error", "未知错误")
                    print(f"  {status_icon} {model}: {error[:50]}...")
        
        # 性能统计
        success_results = [r for r in self.test_results if r["status"] == "success"]
        if success_results:
            durations = [r["duration"] for r in success_results if "duration" in r]
            if durations:
                avg_duration = sum(durations) / len(durations)
                print(f"\n⚡ 平均响应时间: {avg_duration:.2f}秒")
    
    async def run_full_test(self):
        """运行完整测试"""
        print("🧪 LLM Services 真实 API 测试")
        print("=" * 60)
        
        # 1. 加载配置
        if not self.load_config():
            return False
        
        # 2. 设置Provider
        if not await self.setup_providers():
            return False
        
        # 3. 测试所有模型
        await self.test_all_models()
        
        # 4. 测试聚合器
        await self.test_aggregator()
        
        # 5. 打印总结
        self.print_summary()
        
        # 6. 清理
        await self.manager.close_all()
        
        return True


async def main():
    """主函数"""
    try:
        tester = RealAPITester()
        success = await tester.run_full_test()
        
        if success:
            print("\n🎉 测试完成！")
        else:
            print("\n💥 测试失败！")
            print("💡 请检查 deployment/.env 配置文件中的API密钥")
            
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试运行失败: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 