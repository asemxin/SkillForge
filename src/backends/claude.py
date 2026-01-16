"""Claude (Anthropic) 后端实现"""

from anthropic import AsyncAnthropic

from .base import (
    BackendType,
    BaseBackend,
    CompletionRequest,
    CompletionResponse,
    Message,
)


class ClaudeBackend(BaseBackend):
    """Claude API 后端"""

    backend_type = BackendType.CLAUDE
    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str, model: str | None = None):
        super().__init__(api_key, model or self.DEFAULT_MODEL)
        self.client = AsyncAnthropic(api_key=api_key)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """执行补全请求"""
        # 转换消息格式
        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        # 构建请求参数
        kwargs = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "messages": messages,
            "temperature": request.temperature,
        }

        if request.system:
            kwargs["system"] = request.system

        if request.tools:
            kwargs["tools"] = request.tools

        # 调用 API
        response = await self.client.messages.create(**kwargs)

        # 提取内容
        content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return CompletionResponse(
            content=content,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            tool_calls=tool_calls,
            raw_response=response,
        )

    async def stream_complete(self, request: CompletionRequest):
        """流式补全"""
        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        kwargs = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "messages": messages,
            "temperature": request.temperature,
        }

        if request.system:
            kwargs["system"] = request.system

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
