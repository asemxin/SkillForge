"""数据模型定义"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    """运行状态"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # 部分成功


class SkillRun(BaseModel):
    """技能运行记录"""

    id: str = Field(description="运行 ID (UUID)")
    skill_name: str = Field(description="技能名称")
    status: RunStatus = Field(default=RunStatus.PENDING)
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    
    # 执行详情
    backend_used: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    
    # 关联
    report_id: str | None = None

    class Config:
        use_enum_values = True


class SkillResult(BaseModel):
    """技能执行结果"""

    id: str = Field(description="结果 ID (UUID)")
    run_id: str = Field(description="关联的运行 ID")
    skill_name: str = Field(description="技能名称")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 结果数据
    data: dict[str, Any] = Field(default_factory=dict)
    summary: str | None = None
    
    # 元数据
    version: str | None = None
    tags: list[str] = Field(default_factory=list)


class Report(BaseModel):
    """生成的报告"""

    id: str = Field(description="报告 ID (UUID)")
    run_id: str = Field(description="关联的运行 ID")
    skill_name: str = Field(description="技能名称")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 报告内容
    title: str
    content_html: str
    content_markdown: str | None = None
    
    # 文件路径
    file_path: str | None = None
    
    # 元数据
    is_published: bool = False
    published_url: str | None = None


class TrendingTopic(BaseModel):
    """热搜话题（微博热搜专用）"""

    id: str = Field(description="话题 ID (UUID)")
    run_id: str = Field(description="关联的运行 ID")
    fetched_at: datetime = Field(default_factory=datetime.now)
    
    # 话题信息
    rank: int
    title: str
    hot_value: int
    category: str | None = None
    is_hot: bool = False
    is_new: bool = False
    
    # AI 分析结果
    analysis: dict[str, Any] = Field(default_factory=dict)
    sentiment: str | None = None  # positive/negative/neutral
    keywords: list[str] = Field(default_factory=list)


# Supabase 表名映射
TABLE_NAMES = {
    "skill_runs": SkillRun,
    "skill_results": SkillResult,
    "reports": Report,
    "trending_topics": TrendingTopic,
}
