from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import time


class MessageRole(str, Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class Message:
    """聊天消息"""
    role: MessageRole
    content: str


@dataclass
class Function:
    """函数定义"""
    name: str
    description: str
    parameters: Dict[str, Any]


@dataclass
class ChatCompletionRequest:
    """聊天完成请求"""
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None  # 添加top_p属性
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    functions: Optional[List[Function]] = None


@dataclass
class Usage:
    """Token使用情况"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class Choice:
    """完成选择"""
    index: int
    message: Message
    finish_reason: str


@dataclass
class ChatCompletionResponse:
    """聊天完成响应"""
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatCompletionResponse':
        """从字典创建响应对象"""
        choices = [
            Choice(
                index=choice["index"],
                message=Message(
                    role=MessageRole(choice["message"]["role"]),
                    content=choice["message"]["content"]
                ),
                finish_reason=choice["finish_reason"]
            )
            for choice in data["choices"]
        ]
        
        usage = Usage(
            prompt_tokens=data["usage"]["prompt_tokens"],
            completion_tokens=data["usage"]["completion_tokens"],
            total_tokens=data["usage"]["total_tokens"]
        )
        
        return cls(
            id=data["id"],
            object=data["object"],
            created=data["created"],
            model=data["model"],
            choices=choices,
            usage=usage
        )


@dataclass
class StreamChoice:
    """流式响应选择"""
    delta: Message
    index: int
    finish_reason: Optional[str] = None


@dataclass
class StreamResponse:
    """流式响应"""
    id: str
    object: str
    created: int
    model: str
    choices: List[StreamChoice]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamResponse':
        """从字典创建流式响应对象"""
        choices = [
            StreamChoice(
                delta=Message(
                    role=MessageRole(choice["delta"].get("role", "assistant")),
                    content=choice["delta"].get("content", "")
                ),
                index=choice["index"],
                finish_reason=choice.get("finish_reason")
            )
            for choice in data.get("choices", [])
        ]
        
        return cls(
            id=data["id"],
            object=data["object"],
            created=data["created"],
            model=data["model"],
            choices=choices
        )


@dataclass
class ModelConfig:
    """模型配置"""
    model: str
    provider: str
    api_key: str
    base_url: str
    timeout: float = 30.0
    max_retries: int = 3
    max_concurrent_calls: int = 10


@dataclass
class ProviderConfig:
    """Provider配置"""
    provider: str
    models: Dict[str, ModelConfig]

    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """获取指定模型的配置"""
        return self.models.get(model_name)


class LLMError(Exception):
    """LLM相关错误基类"""
    pass


class ModelNotFoundError(LLMError):
    """模型未找到错误"""
    pass


class ProviderNotFoundError(LLMError):
    """Provider未找到错误"""
    pass


class APIError(LLMError):
    """API调用错误"""
    pass 