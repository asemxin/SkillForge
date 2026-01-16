"""技能注册表 - 自动发现和管理技能"""

import importlib
import pkgutil
from pathlib import Path
from typing import Type

from .base import BaseSkill


class SkillRegistry:
    """
    技能注册表
    
    自动发现和注册 src/skills 目录下的所有技能。
    """

    def __init__(self):
        self._skills: dict[str, Type[BaseSkill]] = {}

    def register(self, skill_class: Type[BaseSkill]) -> Type[BaseSkill]:
        """
        注册技能（作为装饰器使用）
        
        示例:
            @registry.register
            class MySkill(BaseSkill):
                ...
        """
        if not issubclass(skill_class, BaseSkill):
            raise TypeError(f"{skill_class} 必须继承 BaseSkill")
        
        self._skills[skill_class.name] = skill_class
        return skill_class

    def get(self, name: str) -> Type[BaseSkill] | None:
        """获取指定名称的技能类"""
        return self._skills.get(name)

    def get_instance(self, name: str) -> BaseSkill | None:
        """获取指定名称的技能实例"""
        skill_class = self.get(name)
        if skill_class:
            return skill_class()
        return None

    def list_all(self) -> list[str]:
        """列出所有已注册的技能名称"""
        return list(self._skills.keys())

    def list_by_tag(self, tag: str) -> list[str]:
        """按标签筛选技能"""
        return [
            name for name, cls in self._skills.items()
            if tag in getattr(cls, "tags", [])
        ]

    def list_scheduled(self) -> list[tuple[str, str]]:
        """列出所有有调度的技能及其 cron 表达式"""
        return [
            (name, cls.schedule)
            for name, cls in self._skills.items()
            if cls.schedule
        ]

    def auto_discover(self) -> None:
        """
        自动发现并注册 skills 目录下的所有技能
        
        遍历当前包下的所有模块，导入后检查是否有 BaseSkill 的子类。
        """
        package_path = Path(__file__).parent
        
        for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
            if module_name.startswith("_") or module_name in ("base", "registry"):
                continue
            
            try:
                module = importlib.import_module(f".{module_name}", package="src.skills")
                
                # 查找模块中的技能类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseSkill)
                        and attr is not BaseSkill
                        and attr.name not in self._skills
                    ):
                        self.register(attr)
            except Exception as e:
                print(f"警告: 加载模块 {module_name} 失败: {e}")

    def __len__(self) -> int:
        return len(self._skills)

    def __contains__(self, name: str) -> bool:
        return name in self._skills


# 全局注册表实例
registry = SkillRegistry()


def skill(cls: Type[BaseSkill]) -> Type[BaseSkill]:
    """
    便捷的技能注册装饰器
    
    示例:
        @skill
        class MySkill(BaseSkill):
            name = "my_skill"
            ...
    """
    return registry.register(cls)
