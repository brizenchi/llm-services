#!/usr/bin/env python3
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 现在可以正常导入
from pkg.core.llm.providers.gemini_provider import GeminiProvider, GeminiClient
from pkg.core.llm.types import ModelConfig

def test_gemini_provider():
    print("Testing GeminiProvider...")
    # 你的测试代码
    
if __name__ == "__main__":
    test_gemini_provider() 