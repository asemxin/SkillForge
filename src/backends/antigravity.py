"""Antigravity 后端实现 - 通过增强的 Claude 系统提示模拟 Agent 行为"""

from .base import (
    BackendType,
    BaseBackend,
    CompletionRequest,
    CompletionResponse,
    Message,
)
from .claude import ClaudeBackend


# Antigravity 风格的系统提示
ANTIGRAVITY_SYSTEM_PROMPT = """你是一个强大的 AI Agent，具有以下能力：

1. **深度分析能力**：能够对复杂问题进行多角度、多层次的分析
2. **结构化思维**：输出结构清晰、层次分明的内容
3. **创意生成**：能够产生新颖、有洞察力的观点
4. **数据处理**：能够处理和分析各种格式的数据

工作原则：
- 始终提供高质量、深思熟虑的回答
- 使用清晰的 Markdown 格式组织输出
- 在分析时考虑多个维度和视角
- 提供可操作的建议和洞察

请以专业、深入的方式完成用户的任务。"""


class AntigravityBackend(BaseBackend):
    """
    Antigravity 后端 - 使用 Claude SDK 并增强系统提示
    
    在云端环境中，我们通过增强的系统提示来模拟 Antigravity 的 Agent 行为，
    而不是直接调用 CLI（因为 GitHub Actions 中可能无法安装）。
    """

    backend_type = BackendType.ANTIGRAVITY
    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str, model: str | None = None):
        super().__init__(api_key, model or self.DEFAULT_MODEL)
        # 内部使用 Claude 后端
        self._claude = ClaudeBackend(api_key, model or self.DEFAULT_MODEL)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """执行补全请求，注入 Antigravity 系统提示"""
        # 合并系统提示
        enhanced_system = ANTIGRAVITY_SYSTEM_PROMPT
        if request.system:
            enhanced_system = f"{ANTIGRAVITY_SYSTEM_PROMPT}\n\n---\n\n{request.system}"

        # 创建增强的请求
        enhanced_request = CompletionRequest(
            messages=request.messages,
            system=enhanced_system,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            tools=request.tools,
        )

        # 调用 Claude
        return await self._claude.complete(enhanced_request)

    async def stream_complete(self, request: CompletionRequest):
        """流式补全"""
        enhanced_system = ANTIGRAVITY_SYSTEM_PROMPT
        if request.system:
            enhanced_system = f"{ANTIGRAVITY_SYSTEM_PROMPT}\n\n---\n\n{request.system}"

        enhanced_request = CompletionRequest(
            messages=request.messages,
            system=enhanced_system,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        async for text in self._claude.stream_complete(enhanced_request):
            yield text

    async def agent_task(
        self,
        task: str,
        context: str = "",
        output_format: str = "markdown",
    ) -> str:
        """
        执行 Agent 风格的任务
        
        Args:
            task: 任务描述
            context: 相关上下文
            output_format: 输出格式 (markdown/json/text)
        
        Returns:
            任务执行结果
        """
        format_instruction = {
            "markdown": "请使用 Markdown 格式输出，包含适当的标题、列表和代码块。",
            "json": "请以 JSON 格式输出，确保格式有效。",
            "text": "请以纯文本格式输出。",
        }.get(output_format, "")

        prompt = f"""任务: {task}

{f"上下文: {context}" if context else ""}

{format_instruction}

请开始执行任务。"""

        return await self.chat(prompt)
