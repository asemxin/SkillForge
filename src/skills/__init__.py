"""Skills 模块"""

from .base import BaseSkill, SkillContext, SkillResult, SkillStatus
from .registry import registry, skill

# 自动发现并注册所有技能
registry.auto_discover()

__all__ = [
    "BaseSkill",
    "SkillContext",
    "SkillResult",
    "SkillStatus",
    "registry",
    "skill",
]
