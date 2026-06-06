from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .content_fetcher import ContentFetcher
from .embedding import EmbeddingService
from .knowledge_base import KnowledgeBase


# ── 种子知识主题定义 ──────────────────────────────────────────

@dataclass
class SeedTopic:
    query: str
    category: str
    lang: str = "zh"


SEED_TOPICS: List[SeedTopic] = [
    # ── 演示设计理论 ──
    SeedTopic("McKinsey presentation methodology pyramid principle", "演示方法", "en"),
    SeedTopic("麦肯锡 金字塔原理 演示方法 结构化思维", "演示方法", "zh"),
    SeedTopic("Minto pyramid principle business presentation structure", "演示方法", "en"),
    SeedTopic("Barbara Minto SCQA framework presentation storytelling", "演示方法", "en"),
    SeedTopic("SCQA 情景冲突问题答案 框架 演示叙事结构", "演示方法", "zh"),
    SeedTopic("McKinsey 麦肯锡 PPT 制作规范 图表使用 排版", "演示规范", "zh"),
    SeedTopic("management consulting presentation best practices slide design", "演示规范", "en"),

    # ── 幻灯片结构与叙事 ──
    SeedTopic("presentation storytelling techniques TED talk structure", "叙事结构", "en"),
    SeedTopic("TED演讲 叙事结构 演示技巧 故事线设计", "叙事结构", "zh"),
    SeedTopic("slide structure narrative arc beginning middle end", "叙事结构", "en"),
    SeedTopic("Nancy Duarte slide:ology presentation design principles", "叙事结构", "en"),
    SeedTopic("Duarte 演示设计 幻灯片设计原则 视觉叙事", "叙事结构", "zh"),
    SeedTopic("如何构建PPT故事线 演示逻辑 信息架构", "叙事结构", "zh"),

    # ── 数据可视化 ──
    SeedTopic("data visualization best practices charts selection guide", "数据可视化", "en"),
    SeedTopic("Edward Tufte data-ink ratio visualization principles", "数据可视化", "en"),
    SeedTopic("数据可视化 最佳实践 图表选择 信息图设计", "数据可视化", "zh"),
    SeedTopic("business charts bar line pie scatter when to use which", "数据可视化", "en"),
    SeedTopic("KPI dashboard design principles executive presentation", "数据可视化", "en"),
    SeedTopic("数据大屏 KPI仪表盘 设计原则 可视化规范", "数据可视化", "zh"),

    # ── 商业分析框架 ──
    SeedTopic("SWOT analysis framework example business strategy", "分析框架", "en"),
    SeedTopic("SWOT分析 框架 案例 企业战略规划", "分析框架", "zh"),
    SeedTopic("PEST PESTLE analysis framework macro environment", "分析框架", "en"),
    SeedTopic("PEST分析 宏观环境 PESTEL 案例讲解", "分析框架", "zh"),
    SeedTopic("Porter five forces industry analysis framework competitive", "分析框架", "en"),
    SeedTopic("波特五力模型 行业分析 竞争分析 案例", "分析框架", "zh"),
    SeedTopic("BCG matrix growth share matrix product portfolio analysis", "分析框架", "en"),
    SeedTopic("波士顿矩阵 BCG 产品组合分析 增长率市场份额", "分析框架", "zh"),
    SeedTopic("balanced scorecard strategy map KPI framework", "分析框架", "en"),
    SeedTopic("平衡计分卡 战略地图 KPI 绩效管理框架", "分析框架", "zh"),
    SeedTopic("business model canvas value proposition design", "分析框架", "en"),
    SeedTopic("商业模式画布 价值主张 精益画布 创业", "分析框架", "zh"),

    # ── 行业分析方法 ──
    SeedTopic("market sizing TAM SAM SOM analysis methodology", "行业分析", "en"),
    SeedTopic("市场规模估算 TAM SAM SOM 分析方法", "行业分析", "zh"),
    SeedTopic("competitive landscape analysis market share benchmarking", "行业分析", "en"),
    SeedTopic("竞争格局分析 市场份额 对标分析 方法", "行业分析", "zh"),
    SeedTopic("industry trend analysis report writing methodology", "行业分析", "en"),
    SeedTopic("行业趋势分析 行业研究报告 方法论 框架", "行业分析", "zh"),
    SeedTopic("艾瑞咨询 行业研究方法论 报告框架", "行业分析", "zh"),

    # ── 路演与融资演示 ──
    SeedTopic("pitch deck structure startup fundraising slide template", "路演融资", "en"),
    SeedTopic("融资路演PPT结构 商业计划书 投资人演讲", "路演融资", "zh"),
    SeedTopic("Sequoia pitch deck template structure fundraising", "路演融资", "en"),
    SeedTopic("YC startup pitch deck advice fundraising presentation", "路演融资", "en"),
    SeedTopic("红杉资本 融资演示 创业项目路演 模板", "路演融资", "zh"),

    # ── 产品演示与销售 ──
    SeedTopic("product demo presentation SaaS sales deck best practices", "产品演示", "en"),
    SeedTopic("产品演示PPT 销售演示 SaaS 最佳实践", "产品演示", "zh"),
    SeedTopic("sales presentation framework solution selling methodology", "产品演示", "en"),

    # ── 学术与教育 ──
    SeedTopic("academic presentation thesis defense slide design", "学术教育", "en"),
    SeedTopic("学术汇报 毕业答辩 PPT设计 论文展示", "学术教育", "zh"),
    SeedTopic("teaching courseware presentation design education", "学术教育", "en"),
    SeedTopic("教学设计 课件制作 教育PPT 培训演示", "学术教育", "zh"),

    # ── 配色排版与视觉设计 ──
    SeedTopic("presentation color palette design principles color theory", "视觉设计", "en"),
    SeedTopic("PPT配色方案 演示设计配色 色彩搭配原则", "视觉设计", "zh"),
    SeedTopic("typography presentation font pairing readability slide design", "视觉设计", "en"),
    SeedTopic("幻灯片排版 版式设计 字体选择 视觉层级", "视觉设计", "zh"),
    SeedTopic("Garr Reynolds Presentation Zen design principles", "视觉设计", "en"),

    # ── 专业技术与工具 ──
    SeedTopic("AI powered presentation generation tools 2024 2025", "技术趋势", "en"),
    SeedTopic("AI PPT 智能生成 人工智能演示工具 2025", "技术趋势", "zh"),
    SeedTopic("大语言模型 内容生成 演示文稿 自动化 PPT", "技术趋势", "zh"),
    SeedTopic("generative AI slide deck creation LLM presentation", "技术趋势", "en"),

    # ── 项目管理与汇报 ──
    SeedTopic("project status report executive summary presentation template", "项目管理", "en"),
    SeedTopic("项目汇报PPT 周报月报 进度报告 模板结构", "项目管理", "zh"),
    SeedTopic("executive presentation summary one-pager best practices", "项目管理", "en"),
    SeedTopic("高层汇报 一页纸报告 摘要演示 最佳实践", "项目管理", "zh"),

    # ── 行业特化 ──
    SeedTopic("healthcare pharmaceutical industry presentation compliance", "行业特化", "en"),
    SeedTopic("医疗医药行业 PPT 演示 合规要求 行业规范", "行业特化", "zh"),
    SeedTopic("financial services banking fintech presentation data security", "行业特化", "en"),
    SeedTopic("金融行业 PPT 数据安全 合规演示 银行证券", "行业特化", "zh"),
    SeedTopic("互联网科技 产品发布 技术架构 演示规范", "行业特化", "zh"),

    # ── 高端咨询报告 ──
    SeedTopic("Gartner Magic Quadrant methodology technology analysis", "高端咨询", "en"),
    SeedTopic("Gartner 魔力象限 技术分析 方法论 报告", "高端咨询", "zh"),
    SeedTopic("McKinsey Global Institute research report methodology", "高端咨询", "en"),
    SeedTopic("BCG Bain consulting deck structure problem solving", "高端咨询", "en"),
]


@dataclass
class BootstrapProgress:
    phase: str = ""
    current: int = 0
    total: int = 0
    message: str = ""
    topics_completed: int = 0
    topics_total: int = 0
    documents_ingested: int = 0
    chunks_ingested: int = 0
    errors: List[str] = field(default_factory=list)
    finished: bool = False


class SeedBootstrapper:
    def __init__(
        self,
        kb: KnowledgeBase,
        embedding: EmbeddingService,
        fetcher: ContentFetcher,
        max_articles_per_topic: int = 3,
        max_topics: int = 0,
    ):
        self._kb = kb
        self._embedding = embedding
        self._fetcher = fetcher
        self._max_articles = max_articles_per_topic
        self._max_topics = max_topics
        self._progress = BootstrapProgress()
        self._on_progress: Optional[Callable[[BootstrapProgress], None]] = None

    @property
    def progress(self) -> BootstrapProgress:
        return self._progress

    def on_progress(self, cb: Callable[[BootstrapProgress], None]):
        self._on_progress = cb

    def _emit(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self._progress, k, v)
        if self._on_progress:
            self._on_progress(self._progress)

    def run(self) -> BootstrapProgress:
        self._progress = BootstrapProgress()
        self._emit(phase="collection_init")

        self._emit(phase="ensure_collection", message="Initializing Milvus collection...")
        self._kb.ensure_collection()

        topics = list(SEED_TOPICS)
        if self._max_topics > 0:
            topics = topics[:self._max_topics]

        self._emit(
            phase="fetching",
            topics_total=len(topics),
            message=f"Starting to fetch {len(topics)} topics...",
        )

        for idx, topic in enumerate(topics):
            self._emit(
                phase="fetching",
                current=idx + 1,
                total=len(topics),
                topics_completed=idx,
                message=f"[{idx + 1}/{len(topics)}] Searching: {topic.query[:80]}",
            )

            try:
                docs = self._fetcher.search_and_fetch(
                    query=topic.query,
                    max_urls=self._max_articles,
                )

                for doc in docs:
                    source = self._make_source(topic.category, doc["url"])
                    metadata = {
                        "category": topic.category,
                        "query": topic.query,
                        "lang": topic.lang,
                        "url": doc["url"],
                        "title": doc["title"],
                    }
                    try:
                        n = self._kb.ingest_text(
                            content=doc["content"],
                            source=source,
                            metadata=metadata,
                        )
                        self._emit(chunks_ingested=self._progress.chunks_ingested + n)
                        self._emit(documents_ingested=self._progress.documents_ingested + 1)
                    except Exception as e:
                        self._progress.errors.append(f"Ingest error [{source}]: {e}")

                self._emit(topics_completed=idx + 1)
                time.sleep(1.0)

            except Exception as e:
                self._progress.errors.append(f"Topic error [{topic.query[:60]}]: {e}")

        self._emit(
            phase="done",
            finished=True,
            message=(
                f"Bootstrapping complete. "
                f"Topics: {self._progress.topics_completed}/{self._progress.topics_total}, "
                f"Documents: {self._progress.documents_ingested}, "
                f"Chunks: {self._progress.chunks_ingested}, "
                f"Errors: {len(self._progress.errors)}"
            ),
        )
        return self._progress

    def _make_source(self, category: str, url: str) -> str:
        import hashlib
        domain = url.split("/")[2] if "//" in url else url
        h = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"seed:{category}:{domain}:{h}"


def create_default_bootstrapper(
    kb: KnowledgeBase,
    embedding: EmbeddingService,
    max_articles_per_topic: int = 3,
    max_topics: int = 0,
) -> SeedBootstrapper:
    return SeedBootstrapper(
        kb=kb,
        embedding=embedding,
        fetcher=ContentFetcher(),
        max_articles_per_topic=max_articles_per_topic,
        max_topics=max_topics,
    )
