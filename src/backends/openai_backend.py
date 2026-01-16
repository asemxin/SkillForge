"""OpenAI 后端实现"""

from openai import AsyncOpenAI

from .base import (
    BackendType,
    BaseBackend,
    CompletionRequest,
    CompletionResponse,
)


class OpenAIBackend(BaseBackend):
    """OpenAI API 后端"""

    backend_type = BackendType.OPENAI
    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, api_key: str, model: str | None = None):
        super().__init__(api_key, model or self.DEFAULT_MODEL)
        self.client = AsyncOpenAI(api_key=api_key)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """执行补全请求"""
        # 构建消息
        messages = []
        
        if request.system:
            messages.append({"role": "system", "content": request.system})
        
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        # 构建请求参数
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        if request.tools:
            kwargs["tools"] = request.tools

        # 调用 API
        response = await self.client.chat.completions.create(**kwargs)

        # 提取工具调用
        tool_calls = []
        if response.choices[0].message.tool_calls:
            for tc in response.choices[0].message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": tc.function.arguments,
                })

        return CompletionResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
            tool_calls=tool_calls,
            raw_response=response,
        )

    async def stream_complete(self, request: CompletionRequest):
        """流式补全"""
        messages = []
        
        if request.system:
            messages.append({"role": "system", "content": request.system})
        
        for msg in request.messages:
            messages.append({"role": msg.role, "content": msg.content})

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
