# LLM Services 测试文档

## 📋 目录结构

```
tests/
├── __init__.py               # 测试包初始化
├── README.md                 # 本文档  
├── run_tests.py              # 统一测试运行器 ⭐
├── api_tests/                # API测试目录
│   ├── __init__.py
│   ├── real_api_test.py      # 完整真实API测试
│   ├── quick_test.py         # 快速API测试 ⚡
│   ├── gemini_test.py        # Gemini专用测试 🆕
│   └── test_all_providers.py # 所有Provider测试 🆕
└── unit_tests/               # 单元测试目录
    ├── __init__.py
    └── simple_test.py        # Mock单元测试
```

## 🚀 快速开始

### 使用新的统一测试运行器（推荐）

```bash
# 运行单元测试（Mock，不消耗API）
python3 tests/run_tests.py unit

# 运行快速API测试
python3 tests/run_tests.py quick

# 运行快速API测试并自定义消息
python3 tests/run_tests.py quick -m "你好，请介绍一下你自己"

# 运行完整API测试
python3 tests/run_tests.py full

# 运行所有测试
python3 tests/run_tests.py all
```

### 直接运行特定测试

```bash
# 单元测试（不消耗API费用）
python3 tests/unit_tests/simple_test.py

# 快速API测试
python3 tests/api_tests/quick_test.py

# 自定义消息的快速测试
python3 tests/api_tests/quick_test.py "你的自定义消息"

# 完整API测试（包含性能统计）
python3 tests/api_tests/real_api_test.py

# 🆕 Gemini专用测试
python3 tests/api_tests/gemini_test.py

# 🆕 所有Provider测试
python3 tests/api_tests/test_all_providers.py
```

## 📊 测试类型说明

### 1. 单元测试 (`unit_tests/`)
- **文件**: `simple_test.py`
- **特点**: 使用Mock，不调用真实API
- **用途**: 验证架构和逻辑
- **费用**: 免费
- **时间**: 10-30秒

### 2. 快速API测试 (`api_tests/quick_test.py`)
- **特点**: 单次真实API调用
- **用途**: 验证API配置和连接
- **费用**: 低（每次几分钱）
- **时间**: 5-15秒

### 3. 完整API测试 (`api_tests/real_api_test.py`)
- **特点**: 多轮测试 + 性能统计
- **用途**: 全面测试和性能分析
- **费用**: 中等（多次API调用）
- **时间**: 60-120秒

### 4. 🆕 Gemini专用测试 (`api_tests/gemini_test.py`)
- **特点**: 专门测试Google Gemini API
- **用途**: 验证Gemini Provider功能
- **费用**: 低（根据Gemini定价）
- **时间**: 30-60秒

### 5. 🆕 所有Provider测试 (`api_tests/test_all_providers.py`)
- **特点**: 测试OpenAI、DeepSeek、Gemini所有Provider
- **用途**: 一次性验证所有API连接
- **费用**: 中等（所有API各一次调用）
- **时间**: 15-30秒

## 🔧 配置要求

确保 `deployment/.env` 文件配置正确：

```bash
# OpenAI配置
OPENAI_API_KEY=sk-your-real-openai-key
OPENAI_API_BASE_URL=https://api.openai.com/v1

# DeepSeek配置
DEEPSEEK_API_KEY=sk-your-real-deepseek-key
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1

# 🆕 Gemini配置
GEMINI_API_KEY=your-real-gemini-key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta

# 启用所有Providers
LLM_ENABLED_PROVIDERS=openai,deepseek,gemini

# 聚合器配置（包含所有模型）
AGGREGATOR_DEFAULT_MODELS=gpt-3.5-turbo,deepseek-chat,gemini-2.0-flash-exp
```

## 💡 使用建议

1. **开发时**: 主要使用 `unit` 测试验证逻辑
2. **API验证**: 使用 `test_all_providers.py` 一次性验证所有API
3. **单独测试**: 使用各Provider的专用测试（如`gemini_test.py`）
4. **性能测试**: 使用 `full` 测试做完整验证
5. **CI/CD**: 使用 `all` 运行完整测试套件

## 🎯 常用命令

```bash
# 日常开发
python3 tests/run_tests.py unit

# 验证所有API配置
python3 tests/api_tests/test_all_providers.py

# 测试特定Provider
python3 tests/api_tests/gemini_test.py

# 测试特定功能
python3 tests/run_tests.py quick -m "测试代码生成功能"

# 完整验证
python3 tests/run_tests.py all
```

## 🆕 Gemini Provider 特性

- ✅ **完全集成**: 使用相同的三层架构
- ✅ **多模型支持**: gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash
- ✅ **流式响应**: 支持实时流式输出
- ✅ **故障转移**: 支持聚合器的自动故障转移
- ✅ **标准接口**: 与OpenAI、DeepSeek使用相同的API

## 📚 相关文档

- 📖 [Gemini Provider配置指南](../GEMINI_SETUP.md)
- 🔗 [Google AI Studio](https://ai.google.dev/)
- 🧪 测试实现: `pkg/core/llm/providers/gemini_provider.py`
- 💡 使用示例: `tests/api_tests/gemini_test.py` 