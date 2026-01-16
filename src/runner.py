"""SkillForge 主执行器"""

import asyncio
import sys
from datetime import datetime
from uuid import uuid4

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .backends import create_backend
from .config import settings
from .database import db, RunStatus
from .reports import ReportGenerator, generate_index
from .skills import registry, SkillContext, SkillStatus

app = typer.Typer(
    name="skillforge",
    help="SkillForge - 云端自动化 AI Agent 平台",
    add_completion=False,
)
console = Console()


def print_banner():
    """打印启动横幅"""
    banner = """
[bold blue]⚡ SkillForge[/bold blue]
[dim]云端自动化 AI Agent 平台[/dim]
    """
    console.print(Panel(banner, border_style="blue"))


@app.command()
def run(
    skill: str = typer.Option(None, "--skill", "-s", help="要执行的技能名称"),
    backend: str = typer.Option(None, "--backend", "-b", help="使用的 AI 后端"),
    all_scheduled: bool = typer.Option(False, "--all-scheduled", help="执行所有定时技能"),
    generate_index_only: bool = typer.Option(False, "--generate-index", help="仅生成索引页"),
):
    """执行技能或生成报告"""
    print_banner()
    
    if generate_index_only:
        _generate_index()
        return
    
    if all_scheduled:
        asyncio.run(_run_all_scheduled(backend))
    elif skill:
        asyncio.run(_run_skill(skill, backend))
    else:
        console.print("[yellow]请指定 --skill 或 --all-scheduled[/yellow]")
        _list_skills()


@app.command("list")
def list_skills():
    """列出所有可用技能"""
    _list_skills()


def _list_skills():
    """列出所有技能"""
    # 确保技能已加载
    from .skills import registry
    
    table = Table(title="可用技能", show_header=True, header_style="bold blue")
    table.add_column("名称", style="cyan")
    table.add_column("描述")
    table.add_column("后端", style="green")
    table.add_column("调度", style="yellow")
    table.add_column("标签", style="dim")
    
    for name in registry.list_all():
        skill_class = registry.get(name)
        if skill_class:
            table.add_row(
                skill_class.name,
                skill_class.description,
                skill_class.default_backend,
                skill_class.schedule or "-",
                ", ".join(skill_class.tags) if skill_class.tags else "-",
            )
    
    console.print(table)


async def _run_skill(skill_name: str, backend_name: str | None = None):
    """执行单个技能"""
    # 获取技能
    skill_instance = registry.get_instance(skill_name)
    if not skill_instance:
        console.print(f"[red]未找到技能: {skill_name}[/red]")
        console.print(f"可用技能: {', '.join(registry.list_all())}")
        return
    
    console.print(f"\n[bold]🚀 执行技能: {skill_name}[/bold]")
    
    # 确定后端
    backend_type = backend_name or skill_instance.default_backend
    api_key = settings.get_backend_api_key(backend_type)
    
    if not api_key:
        console.print(f"[red]未配置 {backend_type} 的 API Key[/red]")
        return
    
    # 创建后端
    backend = create_backend(backend_type, api_key)
    console.print(f"[dim]使用后端: {backend}[/dim]")
    
    # 创建上下文
    run_id = str(uuid4())
    ctx = SkillContext(
        run_id=run_id,
        started_at=datetime.now(),
        backend=backend,
    )
    
    # 记录到数据库（如果配置了）
    if db.is_configured():
        await db.create_run(skill_name)
    
    # 执行
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("执行中...", total=None)
        
        try:
            result = await skill_instance.run(ctx)
            progress.update(task, description="完成!")
        except Exception as e:
            progress.update(task, description=f"[red]失败: {e}[/red]")
            return
    
    # 显示结果
    if result.status == SkillStatus.SUCCESS:
        console.print(f"\n[green]✅ 执行成功[/green]")
        console.print(f"[dim]耗时: {result.duration_seconds:.2f}秒[/dim]")
        
        # 生成报告
        if result.data:
            _generate_report(skill_name, result.data, backend_type)
            
            # 保存到数据库
            if db.is_configured():
                await db.update_run_status(run_id, RunStatus.SUCCESS, finished_at=datetime.now())
                await db.save_result(run_id, skill_name, result.data, result.data.get("summary"))
    else:
        console.print(f"\n[red]❌ 执行失败: {result.error}[/red]")
        if db.is_configured():
            await db.update_run_status(run_id, RunStatus.FAILED, error_message=result.error)


async def _run_all_scheduled(backend_name: str | None = None):
    """执行所有定时技能"""
    scheduled = registry.list_scheduled()
    
    if not scheduled:
        console.print("[yellow]没有配置定时调度的技能[/yellow]")
        return
    
    console.print(f"\n[bold]🚀 执行 {len(scheduled)} 个定时技能[/bold]")
    
    for skill_name, cron in scheduled:
        console.print(f"\n[cyan]--- {skill_name} (cron: {cron}) ---[/cyan]")
        await _run_skill(skill_name, backend_name)
    
    # 生成索引
    _generate_index()


def _generate_report(skill_name: str, data: dict, backend: str):
    """生成 HTML 报告"""
    console.print("\n[bold]📊 生成报告...[/bold]")
    
    generator = ReportGenerator()
    
    # 添加额外信息
    data["backend"] = backend
    
    # 生成报告
    report_path = generator.generate_report(
        skill_name=skill_name,
        title=f"{skill_name} 分析报告",
        data=data,
    )
    
    console.print(f"[green]报告已生成: {report_path}[/green]")
    
    # 生成索引
    index_path = generator.generate_index()
    console.print(f"[green]索引已更新: {index_path}[/green]")


def _generate_index():
    """仅生成索引页"""
    console.print("\n[bold]📊 生成索引页...[/bold]")
    index_path = generate_index()
    console.print(f"[green]索引已生成: {index_path}[/green]")


def main():
    """CLI 入口点"""
    app()


if __name__ == "__main__":
    main()
