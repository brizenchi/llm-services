# Gemini 流式接口测试示例

## 1. 流式聊天接口

### 基本使用
```bash
curl -N --location --request POST 'http://127.0.0.1:8000/api/v1/demo/chat/stream' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer FHDKdhfukFODIHfo3' \
--data-raw '{
    "message": "请用中文写一首关于编程的短诗",
    "model": "gemini-2.5-flash"
}'
```

### 响应格式示例
```
data: {"type": "start", "model": "gemini-2.5-flash", "user_message": "请用中文写一首关于编程的短诗", "timestamp": 1642234567.123}

data: {"type": "content", "content": "代码", "chunk_index": 1, "model": "gemini-2.5-flash", "timestamp": 1642234567.234}

data: {"type": "content", "content": "如诗", "chunk_index": 2, "model": "gemini-2.5-flash", "timestamp": 1642234567.345}

data: {"type": "content", "content": "行间", "chunk_index": 3, "model": "gemini-2.5-flash", "timestamp": 1642234567.456}

data: {"type": "finish", "finish_reason": "stop", "total_content": "代码如诗行间...", "total_chunks": 10, "model": "gemini-2.5-flash", "timestamp": 1642234567.567}

data: {"type": "done", "total_content": "代码如诗行间...", "total_chunks": 10, "model": "gemini-2.5-flash", "user_message": "请用中文写一首关于编程的短诗", "timestamp": 1642234567.678}

data: [DONE]
```

## 2. 流式多轮对话接口

### 基本使用
```bash
curl -N --location --request POST 'http://127.0.0.1:8000/api/v1/demo/chat/stream/multi-turn' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer FHDKdhfukFODIHfo3' \
--data-raw '{
    "messages": [
        {"role": "user", "content": "你好，我是一名软件工程师"},
        {"role": "assistant", "content": "你好！很高兴认识你。作为软件工程师，你主要使用什么编程语言呢？"},
        {"role": "user", "content": "我主要使用Python和JavaScript。你能给我一些关于代码优化的建议吗？"}
    ],
    "model": "gemini-2.5-flash"
}'
```

## 3. 流式响应事件类型

| 事件类型 | 描述 | 字段 |
|---------|------|------|
| `start` | 开始生成回复 | `type`, `model`, `user_message`/`conversation`, `timestamp` |
| `content` | 内容片段 | `type`, `content`, `chunk_index`, `model`, `timestamp` |
| `finish` | 生成完成 | `type`, `finish_reason`, `total_content`, `total_chunks`, `model`, `timestamp` |
| `done` | 任务完成 | `type`, `total_content`, `total_chunks`, `model`, `user_message`/`conversation`, `timestamp` |
| `error` | 错误信息 | `type`, `error`, `user_message`/`conversation`, `model`, `timestamp` |

## 4. 错误处理示例

### 没有权限
```bash
curl -N --location --request POST 'http://127.0.0.1:8000/api/v1/demo/chat/stream' \
--header 'Content-Type: application/json' \
--data-raw '{
    "message": "你好",
    "model": "gemini-2.5-flash"
}'
```

响应：
```json
{"code":401,"message":"请提供访问令牌 (支持 Authorization: Bearer <token> 或 token: <token> 格式)","data":null,"trace_id":"..."}
```

### 错误的 token
```bash
curl -N --location --request POST 'http://127.0.0.1:8000/api/v1/demo/chat/stream' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer wrong-token' \
--data-raw '{
    "message": "你好",
    "model": "gemini-2.5-flash"
}'
```

响应：
```json
{"code":401,"message":"没权限","data":null,"trace_id":"..."}
```

## 5. 注意事项

1. **使用 `-N` 参数**：curl 需要使用 `-N` 参数来禁用输出缓冲，以便实时接收流式数据
2. **认证**：所有流式接口都需要提供有效的 token
3. **Content-Type**：必须设置为 `application/json`
4. **结束标志**：流结束时会发送 `data: [DONE]`
5. **错误处理**：如果发生错误，会在流中发送错误事件

## 6. 使用 Python 测试

```bash
# 运行自动化测试脚本
cd tests/api_tests
python stream_test.py
```

这个脚本会自动测试两种流式接口，并实时显示响应内容。 