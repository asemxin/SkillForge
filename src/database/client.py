"""Supabase 数据库客户端"""

from datetime import datetime
from typing import Any, TypeVar
from uuid import uuid4

from pydantic import BaseModel
from supabase import create_client, Client

from ..config import settings
from .models import SkillRun, SkillResult, Report, TrendingTopic, RunStatus


T = TypeVar("T", bound=BaseModel)


class DatabaseClient:
    """
    Supabase 数据库客户端
    
    封装所有数据库操作，提供类型安全的 CRUD 接口。
    """

    def __init__(self, url: str | None = None, key: str | None = None):
        self.url = url or settings.supabase_url
        self.key = key or settings.supabase_key
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        """延迟初始化 Supabase 客户端"""
        if self._client is None:
            if not self.url or not self.key:
                raise ValueError("Supabase URL 和 Key 未配置")
            self._client = create_client(self.url, self.key)
        return self._client

    def is_configured(self) -> bool:
        """检查是否已配置数据库"""
        return bool(self.url and self.key)

    # ==================== 通用 CRUD ====================

    async def insert(self, table: str, data: dict[str, Any]) -> dict:
        """插入单条记录"""
        result = self.client.table(table).insert(data).execute()
        return result.data[0] if result.data else {}

    async def insert_many(self, table: str, data: list[dict[str, Any]]) -> list[dict]:
        """批量插入记录"""
        result = self.client.table(table).insert(data).execute()
        return result.data

    async def update(self, table: str, id: str, data: dict[str, Any]) -> dict:
        """更新记录"""
        result = self.client.table(table).update(data).eq("id", id).execute()
        return result.data[0] if result.data else {}

    async def get_by_id(self, table: str, id: str) -> dict | None:
        """根据 ID 获取记录"""
        result = self.client.table(table).select("*").eq("id", id).single().execute()
        return result.data

    async def query(
        self,
        table: str,
        filters: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """查询记录"""
        query = self.client.table(table).select("*")
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        if order_by:
            desc = order_by.startswith("-")
            column = order_by.lstrip("-")
            query = query.order(column, desc=desc)
        
        if limit:
            query = query.limit(limit)
        
        result = query.execute()
        return result.data

    # ==================== 技能运行记录 ====================

    async def create_run(self, skill_name: str, params: dict | None = None) -> SkillRun:
        """创建技能运行记录"""
        run = SkillRun(
            id=str(uuid4()),
            skill_name=skill_name,
            status=RunStatus.PENDING,
            params=params or {},
        )
        data = run.model_dump()
        data["started_at"] = data["started_at"].isoformat()
        await self.insert("skill_runs", data)
        return run

    async def update_run_status(
        self,
        run_id: str,
        status: RunStatus,
        error_message: str | None = None,
        finished_at: datetime | None = None,
    ) -> None:
        """更新运行状态"""
        data = {"status": status.value}
        if error_message:
            data["error_message"] = error_message
        if finished_at:
            data["finished_at"] = finished_at.isoformat()
            # 计算时长
            run = await self.get_by_id("skill_runs", run_id)
            if run and run.get("started_at"):
                started = datetime.fromisoformat(run["started_at"])
                data["duration_seconds"] = (finished_at - started).total_seconds()
        
        await self.update("skill_runs", run_id, data)

    async def get_recent_runs(
        self,
        skill_name: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """获取最近的运行记录"""
        filters = {}
        if skill_name:
            filters["skill_name"] = skill_name
        return await self.query(
            "skill_runs",
            filters=filters,
            order_by="-started_at",
            limit=limit,
        )

    # ==================== 技能结果 ====================

    async def save_result(
        self,
        run_id: str,
        skill_name: str,
        data: dict,
        summary: str | None = None,
    ) -> SkillResult:
        """保存技能执行结果"""
        result = SkillResult(
            id=str(uuid4()),
            run_id=run_id,
            skill_name=skill_name,
            data=data,
            summary=summary,
        )
        record = result.model_dump()
        record["created_at"] = record["created_at"].isoformat()
        await self.insert("skill_results", record)
        return result

    # ==================== 报告 ====================

    async def save_report(
        self,
        run_id: str,
        skill_name: str,
        title: str,
        content_html: str,
        content_markdown: str | None = None,
        file_path: str | None = None,
    ) -> Report:
        """保存生成的报告"""
        report = Report(
            id=str(uuid4()),
            run_id=run_id,
            skill_name=skill_name,
            title=title,
            content_html=content_html,
            content_markdown=content_markdown,
            file_path=file_path,
        )
        record = report.model_dump()
        record["created_at"] = record["created_at"].isoformat()
        await self.insert("reports", record)
        return report

    async def get_latest_reports(
        self,
        skill_name: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """获取最新报告"""
        filters = {}
        if skill_name:
            filters["skill_name"] = skill_name
        return await self.query(
            "reports",
            filters=filters,
            order_by="-created_at",
            limit=limit,
        )

    # ==================== 热搜话题 ====================

    async def save_trending_topics(
        self,
        run_id: str,
        topics: list[dict],
    ) -> list[TrendingTopic]:
        """批量保存热搜话题"""
        records = []
        for topic in topics:
            t = TrendingTopic(
                id=str(uuid4()),
                run_id=run_id,
                **topic,
            )
            record = t.model_dump()
            record["fetched_at"] = record["fetched_at"].isoformat()
            records.append(record)
        
        if records:
            await self.insert_many("trending_topics", records)
        
        return [TrendingTopic(**r) for r in records]


# 全局数据库客户端实例
db = DatabaseClient()
