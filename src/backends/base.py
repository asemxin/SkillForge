"""AI 后端抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class BackendType(str, Enum):
    """支持的 AI 后端类型"""

    CLAUDE = "claude"
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTIGRAVITY = "antigravity"


@dataclass
class Message:
    """对话消息"""

    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class CompletionRequest:
    """补全请求"""

    messages: list[Message]
    system: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    tools: list[dict[str, Any]] = field(default_factory=list)
    

@dataclass
class CompletionResponse:
    """补全响应"""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw_response: Any = None


class BaseBackend(ABC):
    """AI 后端抽象基类"""

    backend_type: BackendType
    
    def __init__(self, api_key: str, model: str | None = None):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """执行补全请求"""
        pass

    @abstractmethod
    async def stream_complete(self, request: CompletionRequest):
        """流式补全（生成器）"""
        pass

    async def chat(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """简化的聊天接口"""
        request = CompletionRequest(
            messages=[Message(role="user", content=prompt)],
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        response = await self.complete(request)
        return response.content

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model}>"
