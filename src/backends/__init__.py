"""AI 后端模块 - 统一的多后端接口"""

from .base import (
    BackendType,
    BaseBackend,
    CompletionRequest,
    CompletionResponse,
    Message,
)
from .claude import ClaudeBackend
from .gemini import GeminiBackend
from .openai_backend import OpenAIBackend
from .antigravity import AntigravityBackend


def create_backend(
    backend_type: str | BackendType,
    api_key: str,
    model: str | None = None,
) -> BaseBackend:
    """
    工厂函数：创建指定类型的后端实例
    
    Args:
        backend_type: 后端类型 (claude/gemini/openai/antigravity)
        api_key: API Key
        model: 可选的模型名称
    
    Returns:
        后端实例
    
    Raises:
        ValueError: 不支持的后端类型
    """
    if isinstance(backend_type, str):
        backend_type = BackendType(backend_type.lower())

    backend_map = {
        BackendType.CLAUDE: ClaudeBackend,
        BackendType.GEMINI: GeminiBackend,
        BackendType.OPENAI: OpenAIBackend,
        BackendType.ANTIGRAVITY: AntigravityBackend,
    }

    backend_class = backend_map.get(backend_type)
    if not backend_class:
        raise ValueError(f"不支持的后端类型: {backend_type}")

    return backend_class(api_key, model)


__all__ = [
    "BackendType",
    "BaseBackend",
    "CompletionRequest",
    "CompletionResponse",
    "Message",
    "ClaudeBackend",
    "GeminiBackend",
    "OpenAIBackend",
    "AntigravityBackend",
    "create_backend",
]
