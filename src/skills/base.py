"""Skills 基类定义"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..backends import BaseBackend, create_backend
from ..config import settings


class SkillStatus(str, Enum):
    """技能执行状态"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SkillContext:
    """技能执行上下文"""

    run_id: str  # 本次运行的唯一 ID
    started_at: datetime
    backend: BaseBackend  # AI 后端实例
    params: dict[str, Any] = field(default_factory=dict)  # 运行时参数
    data: dict[str, Any] = field(default_factory=dict)  # 共享数据


@dataclass
class SkillResult:
    """技能执行结果"""

    status: SkillStatus
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    
    @property
    def duration_seconds(self) -> float | None:
        """执行时长（秒）"""
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None


class BaseSkill(ABC):
    """
    技能基类
    
    所有技能都应该继承此类并实现 execute 方法。
    
    示例:
        class MySkill(BaseSkill):
            name = "my_skill"
            description = "我的技能"
            
            async def execute(self, ctx: SkillContext) -> SkillResult:
                # 使用 AI 后端
                result = await ctx.backend.chat("Hello!")
                return SkillResult(status=SkillStatus.SUCCESS, data={"response": result})
    """

    # 子类必须覆盖这些属性
    name: str = "base_skill"
    description: str = "技能描述"
    version: str = "1.0.0"
    
    # 默认使用的 AI 后端
    default_backend: str = "antigravity"
    
    # Cron 调度表达式（可选）
    schedule: str | None = None
    
    # 标签，用于分类
    tags: list[str] = []

    def __init__(self):
        self._backend: BaseBackend | None = None

    def get_backend(self) -> BaseBackend:
        """获取或创建 AI 后端实例"""
        if self._backend is None:
            backend_type = self.default_backend
            api_key = settings.get_backend_api_key(backend_type)
            if not api_key:
                raise ValueError(f"未配置 {backend_type} 的 API Key")
            self._backend = create_backend(backend_type, api_key)
        return self._backend

    @abstractmethod
    async def execute(self, ctx: SkillContext) -> SkillResult:
        """
        执行技能逻辑
        
        Args:
            ctx: 执行上下文，包含运行 ID、后端实例、参数等
        
        Returns:
            执行结果
        """
        pass

    async def before_execute(self, ctx: SkillContext) -> None:
        """执行前钩子，可选覆盖"""
        pass

    async def after_execute(self, ctx: SkillContext, result: SkillResult) -> None:
        """执行后钩子，可选覆盖"""
        pass

    async def run(self, ctx: SkillContext) -> SkillResult:
        """
        运行技能的完整流程
        
        包含 before_execute -> execute -> after_execute
        """
        result = SkillResult(status=SkillStatus.RUNNING, started_at=datetime.now())
        
        try:
            await self.before_execute(ctx)
            result = await self.execute(ctx)
            result.started_at = ctx.started_at
            result.finished_at = datetime.now()
            await self.after_execute(ctx, result)
        except Exception as e:
            result.status = SkillStatus.FAILED
            result.error = str(e)
            result.finished_at = datetime.now()
        
        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name}>"
