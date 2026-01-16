"""微博热搜分析技能"""

import json
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from .base import BaseSkill, SkillContext, SkillResult, SkillStatus
from .registry import skill


@skill
class WeiboTrendingSkill(BaseSkill):
    """
    微博热搜分析技能
    
    工作流程：
    1. 获取微博热搜榜单
    2. 对每个热点进行 AI 深度分析
    3. 生成洞察报告
    """

    name = "weibo_trending"
    description = "获取并分析微博热搜榜，生成深度洞察报告"
    version = "1.0.0"
    default_backend = "antigravity"
    schedule = "0 */6 * * *"  # 每6小时运行一次
    tags = ["social", "trending", "analysis"]

    # 分析的热搜数量
    MAX_TOPICS = 10

    async def execute(self, ctx: SkillContext) -> SkillResult:
        """执行微博热搜分析"""
        try:
            # Step 1: 获取热搜数据
            trending_list = await self._fetch_trending()
            if not trending_list:
                return SkillResult(
                    status=SkillStatus.FAILED,
                    error="获取热搜数据失败",
                )

            # Step 2: AI 分析每个热点
            analyzed_topics = []
            for topic in trending_list[: self.MAX_TOPICS]:
                analysis = await self._analyze_topic(ctx.backend, topic)
                analyzed_topics.append({
                    **topic,
                    "analysis": analysis,
                })

            # Step 3: 生成综合洞察
            summary = await self._generate_summary(ctx.backend, analyzed_topics)

            return SkillResult(
                status=SkillStatus.SUCCESS,
                data={
                    "topics": analyzed_topics,
                    "summary": summary,
                    "fetched_at": datetime.now().isoformat(),
                    "total_count": len(trending_list),
                    "analyzed_count": len(analyzed_topics),
                },
            )

        except Exception as e:
            return SkillResult(
                status=SkillStatus.FAILED,
                error=str(e),
            )

    async def _fetch_trending(self) -> list[dict]:
        """获取微博热搜榜单"""
        # 使用公开 API 或爬虫获取
        # 这里使用一个模拟的实现，实际部署时需要替换为真实数据源
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # 尝试从微博热搜 API 获取
                # 注意：这是一个示例 URL，实际需要使用有效的数据源
                response = await client.get(
                    "https://weibo.com/ajax/side/hotSearch",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/json",
                    },
                )
                
                if response.status_code == 200:
                    data = response.json()
                    realtime = data.get("data", {}).get("realtime", [])
                    return [
                        {
                            "rank": i + 1,
                            "title": item.get("word", ""),
                            "hot_value": item.get("num", 0),
                            "category": item.get("category", ""),
                            "is_hot": item.get("is_hot", 0) == 1,
                            "is_new": item.get("is_new", 0) == 1,
                        }
                        for i, item in enumerate(realtime)
                    ]
        except Exception:
            pass

        # 如果 API 失败，返回模拟数据（用于测试）
        return self._get_mock_data()

    def _get_mock_data(self) -> list[dict]:
        """获取模拟数据（用于测试）"""
        return [
            {"rank": 1, "title": "AI技术突破", "hot_value": 1500000, "category": "科技", "is_hot": True, "is_new": False},
            {"rank": 2, "title": "新能源汽车销量创新高", "hot_value": 1200000, "category": "财经", "is_hot": True, "is_new": True},
            {"rank": 3, "title": "春节假期安排公布", "hot_value": 1000000, "category": "社会", "is_hot": False, "is_new": True},
            {"rank": 4, "title": "热门电影票房破10亿", "hot_value": 900000, "category": "娱乐", "is_hot": True, "is_new": False},
            {"rank": 5, "title": "国际形势最新动态", "hot_value": 800000, "category": "国际", "is_hot": False, "is_new": False},
        ]

    async def _analyze_topic(self, backend, topic: dict) -> dict:
        """使用 AI 分析单个热点"""
        prompt = f"""请分析以下微博热搜话题：

话题：{topic['title']}
热度值：{topic['hot_value']:,}
分类：{topic.get('category', '未知')}

请从以下维度进行分析：
1. **话题背景**：简要说明话题的背景和起源
2. **舆论倾向**：分析公众对此话题的主要态度
3. **热度原因**：解释为什么这个话题会上热搜
4. **潜在影响**：分析该话题可能带来的社会影响
5. **发展预测**：预测话题未来的发展趋势

请用 JSON 格式返回分析结果，包含以下字段：
- background: 话题背景（string）
- sentiment: 舆论倾向（positive/negative/neutral）
- sentiment_reason: 倾向原因（string）
- hot_reason: 热度原因（string）
- impact: 潜在影响（string）
- prediction: 发展预测（string）
- keywords: 关键词列表（array of strings）
"""

        try:
            response = await backend.chat(
                prompt,
                system="你是一个专业的舆情分析师，擅长从多角度分析社会热点话题。请始终以 JSON 格式回复。",
                temperature=0.3,
            )
            
            # 尝试解析 JSON
            # 去除可能的 markdown 代码块标记
            json_str = response.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("\n", 1)[1]
            if json_str.endswith("```"):
                json_str = json_str.rsplit("```", 1)[0]
            
            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            # 如果无法解析 JSON，返回原始文本
            return {"raw_analysis": response}
        except Exception as e:
            return {"error": str(e)}

    async def _generate_summary(self, backend, topics: list[dict]) -> str:
        """生成综合洞察报告"""
        topics_text = "\n".join([
            f"{t['rank']}. {t['title']} (热度: {t['hot_value']:,})"
            for t in topics
        ])

        prompt = f"""基于以下微博热搜榜单，生成一份综合洞察报告：

{topics_text}

请从以下维度生成报告：
1. **今日热点概述**：总结今日舆论场的主要特征
2. **话题分类分布**：分析各类话题的占比和特点
3. **舆情风向**：识别主要的舆论情绪和倾向
4. **值得关注**：指出最值得关注的2-3个话题及原因
5. **趋势洞察**：从热搜榜单中发现的趋势性信号

请用结构清晰的 Markdown 格式输出报告。"""

        return await backend.chat(
            prompt,
            system="你是一个资深的舆情分析专家，善于从碎片化信息中提炼价值洞察。",
            temperature=0.5,
        )
