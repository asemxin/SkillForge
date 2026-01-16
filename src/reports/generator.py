"""报告生成器"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import settings
from ..skills import registry


class ReportGenerator:
    """
    HTML 报告生成器
    
    使用 Jinja2 模板生成 Apple 风格的 HTML 报告。
    """

    def __init__(self, output_dir: str | None = None):
        self.output_dir = Path(output_dir or settings.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 模板目录
        template_dir = Path(__file__).parent / "templates"
        static_dir = Path(__file__).parent / "static"
        
        # 初始化 Jinja2
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        
        # 复制静态资源
        self._copy_static(static_dir)

    def _copy_static(self, static_dir: Path) -> None:
        """复制静态资源到输出目录"""
        output_static = self.output_dir / "static"
        if output_static.exists():
            shutil.rmtree(output_static)
        shutil.copytree(static_dir, output_static)

    def _static_url(self, filename: str) -> str:
        """生成静态资源 URL"""
        return f"static/{filename}"

    def _render_markdown(self, text: str) -> str:
        """将 Markdown 转换为 HTML"""
        return markdown.markdown(
            text,
            extensions=["tables", "fenced_code", "nl2br"],
        )

    def generate_report(
        self,
        skill_name: str,
        title: str,
        data: dict[str, Any],
        template: str = "report.html",
    ) -> Path:
        """
        生成技能执行报告
        
        Args:
            skill_name: 技能名称
            title: 报告标题
            data: 报告数据
            template: 使用的模板
        
        Returns:
            生成的报告文件路径
        """
        now = datetime.now()
        
        # 处理 summary (Markdown -> HTML)
        summary_html = ""
        if "summary" in data:
            summary_html = self._render_markdown(data["summary"])
        
        # 准备模板上下文
        context = {
            "title": title,
            "skill_name": skill_name,
            "report_date": now.strftime("%Y年%m月%d日 %H:%M"),
            "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": self._format_duration(data.get("duration_seconds", 0)),
            "backend": data.get("backend", "AI"),
            "summary": summary_html,
            "topics": data.get("topics", []),
            "total_count": data.get("total_count", 0),
            "analyzed_count": data.get("analyzed_count", 0),
            "static_url": self._static_url,
        }
        
        # 渲染模板
        tpl = self.env.get_template(template)
        html = tpl.render(**context)
        
        # 保存文件
        filename = f"{skill_name}_{now.strftime('%Y%m%d_%H%M%S')}.html"
        output_path = self.output_dir / filename
        output_path.write_text(html, encoding="utf-8")
        
        return output_path

    def generate_index(self, reports: list[dict[str, Any]] | None = None) -> Path:
        """
        生成索引页面
        
        Args:
            reports: 报告列表，每个包含 {url, skill_name, title, date, summary}
        
        Returns:
            索引页面路径
        """
        # 扫描输出目录获取报告列表
        if reports is None:
            reports = self._scan_reports()
        
        # 获取已注册的技能
        skills = []
        for name in registry.list_all():
            skill_class = registry.get(name)
            if skill_class:
                skills.append({
                    "name": skill_class.name,
                    "description": skill_class.description,
                    "schedule": skill_class.schedule,
                    "tags": skill_class.tags,
                })
        
        # 渲染模板
        context = {
            "reports": reports,
            "skills": skills,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "static_url": self._static_url,
        }
        
        tpl = self.env.get_template("index.html")
        html = tpl.render(**context)
        
        # 保存
        output_path = self.output_dir / "index.html"
        output_path.write_text(html, encoding="utf-8")
        
        return output_path

    def _scan_reports(self) -> list[dict[str, Any]]:
        """扫描输出目录获取已生成的报告"""
        reports = []
        for file in sorted(self.output_dir.glob("*.html"), reverse=True):
            if file.name == "index.html":
                continue
            
            # 解析文件名: skill_name_YYYYMMDD_HHMMSS.html
            parts = file.stem.rsplit("_", 2)
            if len(parts) >= 3:
                skill_name = parts[0]
                date_str = parts[1]
                time_str = parts[2]
                try:
                    dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    reports.append({
                        "url": file.name,
                        "skill_name": skill_name,
                        "title": f"{skill_name} 报告",
                        "date": dt.strftime("%Y-%m-%d %H:%M"),
                        "summary": "",
                    })
                except ValueError:
                    pass
        
        return reports[:20]  # 最多返回20个

    def _format_duration(self, seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"


# 便捷函数
def generate_report(
    skill_name: str,
    title: str,
    data: dict[str, Any],
    output_dir: str | None = None,
) -> Path:
    """生成报告的便捷函数"""
    generator = ReportGenerator(output_dir)
    return generator.generate_report(skill_name, title, data)


def generate_index(output_dir: str | None = None) -> Path:
    """生成索引页的便捷函数"""
    generator = ReportGenerator(output_dir)
    return generator.generate_index()
