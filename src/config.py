"""配置管理 - 从环境变量读取所有配置"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，优先从环境变量读取"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # AI Backends
    anthropic_api_key: str = Field(default="", description="Anthropic API Key")
    google_api_key: str = Field(default="", description="Google Gemini API Key")
    openai_api_key: str = Field(default="", description="OpenAI API Key")

    # Default AI Backend
    default_backend: Literal["claude", "gemini", "openai", "antigravity"] = Field(
        default="claude", description="默认使用的 AI 后端"
    )

    # AI Model Settings
    claude_model: str = Field(default="claude-sonnet-4-20250514", description="Claude 模型")
    gemini_model: str = Field(default="gemini-2.0-flash", description="Gemini 模型")
    openai_model: str = Field(default="gpt-4o", description="OpenAI 模型")

    # Supabase
    supabase_url: str = Field(default="", description="Supabase 项目 URL")
    supabase_key: str = Field(default="", description="Supabase anon/service key")

    # Output
    output_dir: str = Field(default="output", description="报告输出目录")
    
    # Execution
    max_concurrent_skills: int = Field(default=3, description="最大并发技能数")
    skill_timeout: int = Field(default=300, description="单个技能超时时间(秒)")

    def get_backend_api_key(self, backend: str) -> str:
        """获取指定后端的 API Key"""
        key_map = {
            "claude": self.anthropic_api_key,
            "gemini": self.google_api_key,
            "openai": self.openai_api_key,
            "antigravity": self.anthropic_api_key,  # Antigravity 使用 Claude
        }
        return key_map.get(backend, "")

    def validate_backend(self, backend: str) -> bool:
        """验证指定后端是否可用（有 API Key）"""
        return bool(self.get_backend_api_key(backend))


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 便捷访问
settings = get_settings()
