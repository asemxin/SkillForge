"""Google Gemini 后端实现"""

import google.generativeai as genai

from .base import (
    BackendType,
    BaseBackend,
    CompletionRequest,
    CompletionResponse,
)


class GeminiBackend(BaseBackend):
    """Gemini API 后端"""

    backend_type = BackendType.GEMINI
    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, api_key: str, model: str | None = None):
        super().__init__(api_key, model or self.DEFAULT_MODEL)
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(self.model)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """执行补全请求"""
        # 构建内容
        contents = []
        
        # 添加系统提示（作为第一条用户消息的前缀）
        system_prefix = f"{request.system}\n\n" if request.system else ""
        
        for i, msg in enumerate(request.messages):
            content = msg.content
            # 将系统提示添加到第一条用户消息
            if i == 0 and msg.role == "user" and system_prefix:
                content = system_prefix + content
            
            role = "user" if msg.role == "user" else "model"
            contents.append({"role": role, "parts": [content]})

        # 配置生成参数
        generation_config = genai.GenerationConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
        )

        # 调用 API
        response = await self.client.generate_content_async(
            contents,
            generation_config=generation_config,
        )

        # 提取使用统计
        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
            }

        return CompletionResponse(
            content=response.text,
            model=self.model,
            usage=usage,
            raw_response=response,
        )

    async def stream_complete(self, request: CompletionRequest):
        """流式补全"""
        contents = []
        system_prefix = f"{request.system}\n\n" if request.system else ""
        
        for i, msg in enumerate(request.messages):
            content = msg.content
            if i == 0 and msg.role == "user" and system_prefix:
                content = system_prefix + content
            
            role = "user" if msg.role == "user" else "model"
            contents.append({"role": role, "parts": [content]})

        generation_config = genai.GenerationConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
        )

        response = await self.client.generate_content_async(
            contents,
            generation_config=generation_config,
            stream=True,
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text
