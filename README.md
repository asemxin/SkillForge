# ⚡ SkillForge

**云端自动化 AI Agent 平台** - 基于 GitHub Actions 的定时任务调度，支持多种 AI 后端，自动执行 Skills 并生成精美报告。

## ✨ 特性

- 🤖 **多 AI 后端支持** - Claude, Gemini, OpenAI, Antigravity
- ⏰ **定时调度** - 基于 GitHub Actions 的 Cron 定时执行
- 🧩 **可扩展 Skills** - 标准化的技能接口，易于开发新技能
- 📊 **Apple 风格报告** - 极简高端的 HTML 报告设计
- 💾 **数据持久化** - 支持 Supabase 数据库存储
- 🚀 **自动部署** - 报告自动发布到 GitHub Pages

## 📁 项目结构

```
skillforge/
├── .github/workflows/      # GitHub Actions 工作流
│   ├── scheduler.yml       # 主调度器（定时+手动）
│   └── deploy-pages.yml    # GitHub Pages 部署
├── src/
│   ├── backends/           # AI 后端抽象层
│   │   ├── claude.py       # Claude SDK
│   │   ├── gemini.py       # Gemini API
│   │   ├── openai_backend.py
│   │   └── antigravity.py  # Antigravity 模拟
│   ├── skills/             # 技能模块
│   │   ├── base.py         # 技能基类
│   │   ├── registry.py     # 技能注册表
│   │   └── weibo_trending.py  # 微博热搜示例
│   ├── database/           # 数据层
│   │   ├── models.py       # 数据模型
│   │   └── client.py       # Supabase 客户端
│   ├── reports/            # 报告生成
│   │   ├── templates/      # HTML 模板
│   │   ├── static/         # CSS/JS
│   │   └── generator.py    # 报告生成器
│   ├── config.py           # 配置管理
│   └── runner.py           # 主执行器
├── output/                 # 生成的报告
├── requirements.txt
└── pyproject.toml
```

## 🚀 快速开始

### 1. 本地运行

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/skillforge.git
cd skillforge

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Keys

# 列出可用技能
python -m src.runner list

# 执行技能
python -m src.runner --skill weibo_trending

# 使用指定后端
python -m src.runner --skill weibo_trending --backend gemini
```

### 2. GitHub Actions 部署

1. **Fork 本仓库**

2. **配置 Secrets**
   
   在仓库 Settings > Secrets and variables > Actions 中添加：
   
   | Secret | 说明 |
   |--------|------|
   | `ANTHROPIC_API_KEY` | Claude API Key |
   | `GOOGLE_API_KEY` | Gemini API Key |
   | `OPENAI_API_KEY` | OpenAI API Key |
   | `SUPABASE_URL` | Supabase 项目 URL |
   | `SUPABASE_KEY` | Supabase anon key |

3. **启用 GitHub Pages**
   
   Settings > Pages > Source 选择 `gh-pages` 分支

4. **手动触发测试**
   
   Actions > SkillForge Scheduler > Run workflow

## 🧩 开发新技能

创建新技能非常简单：

```python
# src/skills/my_skill.py
from .base import BaseSkill, SkillContext, SkillResult, SkillStatus
from .registry import skill

@skill
class MySkill(BaseSkill):
    name = "my_skill"
    description = "我的自定义技能"
    default_backend = "claude"
    schedule = "0 8 * * *"  # 每天8点执行
    tags = ["custom"]

    async def execute(self, ctx: SkillContext) -> SkillResult:
        # 使用 AI 后端
        response = await ctx.backend.chat("你好，请帮我...")
        
        return SkillResult(
            status=SkillStatus.SUCCESS,
            data={
                "result": response,
                "summary": "执行摘要...",
            },
        )
```

## 🎨 自定义报告样式

报告模板位于 `src/reports/templates/`，使用 Jinja2 语法：

- `base.html` - 基础布局
- `report.html` - 报告页面
- `index.html` - 索引页面

CSS 样式位于 `src/reports/static/style.css`，采用 CSS 变量便于自定义：

```css
:root {
    --accent-primary: #0a84ff;    /* 主色调 */
    --bg-primary: #000000;        /* 背景色 */
    --text-primary: #f5f5f7;      /* 文字色 */
}
```

## 📊 数据库 Schema

使用 Supabase 时，需要创建以下表：

```sql
-- 技能运行记录
CREATE TABLE skill_runs (
    id UUID PRIMARY KEY,
    skill_name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    duration_seconds FLOAT,
    backend_used TEXT,
    params JSONB DEFAULT '{}',
    error_message TEXT,
    report_id UUID
);

-- 技能执行结果
CREATE TABLE skill_results (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES skill_runs(id),
    skill_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    data JSONB DEFAULT '{}',
    summary TEXT,
    version TEXT,
    tags TEXT[] DEFAULT '{}'
);

-- 生成的报告
CREATE TABLE reports (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES skill_runs(id),
    skill_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    title TEXT NOT NULL,
    content_html TEXT,
    content_markdown TEXT,
    file_path TEXT,
    is_published BOOLEAN DEFAULT FALSE,
    published_url TEXT
);

-- 热搜话题（可选）
CREATE TABLE trending_topics (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES skill_runs(id),
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    rank INT,
    title TEXT NOT NULL,
    hot_value INT,
    category TEXT,
    is_hot BOOLEAN DEFAULT FALSE,
    is_new BOOLEAN DEFAULT FALSE,
    analysis JSONB DEFAULT '{}',
    sentiment TEXT,
    keywords TEXT[] DEFAULT '{}'
);
```

## 🔧 配置说明

所有配置通过环境变量读取：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ANTHROPIC_API_KEY` | Claude API Key | - |
| `GOOGLE_API_KEY` | Gemini API Key | - |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `SUPABASE_URL` | Supabase URL | - |
| `SUPABASE_KEY` | Supabase Key | - |
| `DEFAULT_BACKEND` | 默认 AI 后端 | claude |
| `OUTPUT_DIR` | 报告输出目录 | output |

## 📝 License

MIT

---

**Made with ⚡ by SkillForge**
