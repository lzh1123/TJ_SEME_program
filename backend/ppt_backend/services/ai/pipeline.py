from __future__ import annotations

from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from ...domain.dsl import (
    AgendaSlideDSL,
    ArchitectureSlideDSL,
    ChartSlideDSL,
    ChartSemantic,
    ChartSeries,
    ComparisonSide,
    ComparisonSlideDSL,
    CoverSlideDSL,
    DividerSlideDSL,
    KPIItem,
    KpiSlideDSL,
    MultiColumnSlideDSL,
    PresentationDSL,
    ProcessFlowSlideDSL,
    ProcessStep,
    QuoteSlideDSL,
    RoadmapPhase,
    RoadmapSlideDSL,
    SwotBlock,
    SwotSlideDSL,
    TeamMember,
    TeamSlideDSL,
    TextSlideDSL,
    TimelineEvent,
    TimelineSlideDSL,
)
from ...domain.ids import new_id
from ...domain.theme import get_theme_tokens
from .client import invoke_llm_text, make_llm, parse_model
from .schemas import IntentAnalysis, PresentationPlan


class AiPipeline:
    def __init__(self):
        self._llm = None
        try:
            self._llm = make_llm()
        except Exception:
            self._llm = None

    def analyze_intent(self, topic: str) -> IntentAnalysis:
        if not self._llm:
            raise RuntimeError("LLM not configured")
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是资深 PPT 规划助手。你只输出 JSON，不要输出任何解释文字。\n"
                    "任务：对用户主题做意图分析，给出 audience/goal/tone/slideCount/preferredTheme。\n"
                    "preferredTheme 只能是 modern_blue/paper_light/academic_gray/minimal_black 或 null。",
                ),
                ("human", "{topic}"),
            ]
        )
        raw = invoke_llm_text(self._llm, prompt, {"topic": topic})
        return parse_model(IntentAnalysis, raw)

    def plan_presentation(self, analysis: IntentAnalysis) -> PresentationPlan:
        if not self._llm:
            raise RuntimeError("LLM not configured")
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是资深 PPT 结构规划助手。你只输出 JSON，不要输出任何解释文字。\n"
                    "任务：基于 topic/audience/goal/tone/slideCount 规划 slides 列表。\n"
                    "slides 中每个元素包含 id/intent/section/title/purpose。\n"
                    "intent 必须从以下集合选择：cover/agenda/text/timeline/kpi/comparison/swot/roadmap/process_flow/chart/multi_column/architecture/quote/divider/team。",
                ),
                ("human", "{analysis_json}"),
            ]
        )
        raw = invoke_llm_text(self._llm, prompt, {"analysis_json": analysis.model_dump_json(by_alias=True)})
        return parse_model(PresentationPlan, raw)

    def generate_dsl(self, topic: str, theme: Optional[str] = None) -> PresentationDSL:
        if not topic:
            raise ValueError("topic required")

        if not self._llm:
            return self._fallback(topic, theme)

        try:
            analysis = self.analyze_intent(topic)
            plan = self.plan_presentation(analysis)
        except Exception:
            return self._fallback(topic, theme)

        theme_name = theme or plan.theme or analysis.preferred_theme or "modern_blue"
        _ = get_theme_tokens(theme_name)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是 PPT DSL Generator。你只输出 JSON，不要输出任何解释文字。\n"
                    "你必须输出 PresentationDSL：包含 title/audience/tone/theme/slides。\n"
                    "slides 是语义化页面 DSL，使用 intent 作为 discriminant。\n"
                    "严格禁止输出任何布局字段：x/y/w/h/fontSize/templateId/坐标/尺寸。\n"
                    "只输出结构化语义数据（如 items/events/phases/steps/columns/layers 等）。",
                ),
                ("human", "topic: {topic}\nanalysis: {analysis_json}\nplan: {plan_json}\ntheme: {theme_name}"),
            ]
        )
        raw = invoke_llm_text(
            self._llm,
            prompt,
            {
                "topic": topic,
                "analysis_json": analysis.model_dump_json(by_alias=True),
                "plan_json": plan.model_dump_json(),
                "theme_name": theme_name,
            },
        )
        try:
            dsl = parse_model(PresentationDSL, raw)
        except Exception:
            return self._fallback(topic, theme_name)
        dsl.theme = theme_name
        if not dsl.title:
            dsl.title = plan.title or topic
        if not dsl.slides:
            return self._fallback(topic, theme_name)
        return dsl

    def _fallback(self, topic: str, theme: Optional[str]) -> PresentationDSL:
        theme_name = theme or "modern_blue"
        return PresentationDSL(
            title=topic,
            audience="通用受众",
            tone="清晰、教学",
            theme=theme_name,
            slides=[
                CoverSlideDSL(
                    id=new_id("slide"),
                    intent="cover",
                    section="封面",
                    title=topic,
                    subtitle="AI + DSL + Renderer 驱动的演示生成",
                    highlights=["语义 DSL", "组件化渲染", "可编辑 RenderTree", "python-pptx 导出"],
                ),
                AgendaSlideDSL(
                    id=new_id("slide"),
                    intent="agenda",
                    section="目录",
                    title="内容导航",
                    items=["背景与目标", "核心架构", "DSL 设计", "渲染与编辑", "导出与扩展"],
                ),
                TextSlideDSL(
                    id=new_id("slide"),
                    intent="text",
                    section="背景与目标",
                    title="为什么需要 DSL + Renderer",
                    bullets=[
                        "AI 只负责内容规划，不输出布局",
                        "Renderer 负责布局、样式、视觉结构",
                        "RenderTree JSON 用于实时预览与编辑",
                    ],
                ),
                TimelineSlideDSL(
                    id=new_id("slide"),
                    intent="timeline",
                    section="渲染流程",
                    title="端到端 Pipeline",
                    events=[
                        TimelineEvent(label="User Input", detail="主题/约束"),
                        TimelineEvent(label="AI Pipeline", detail="意图→结构→DSL"),
                        TimelineEvent(label="Render Engine", detail="组件规划→布局→主题"),
                        TimelineEvent(label="Edit", detail="组件拖拽/改文案/换主题"),
                        TimelineEvent(label="Export", detail="RenderTree→PPTX"),
                    ],
                ),
                KpiSlideDSL(
                    id=new_id("slide"),
                    intent="kpi",
                    section="能力",
                    title="系统能力 KPI",
                    items=[
                        KPIItem(label="预览延迟", value="< 1s"),
                        KPIItem(label="编辑粒度", value="Component"),
                        KPIItem(label="导出链路", value="RenderTree→PPTX"),
                    ],
                ),
                SwotSlideDSL(
                    id=new_id("slide"),
                    intent="swot",
                    section="分析",
                    title="SWOT：AI PPT Generator",
                    swot=SwotBlock(
                        strengths=["语义与视觉解耦", "可编辑", "插件化扩展"],
                        weaknesses=["初期组件有限", "布局算法需迭代"],
                        opportunities=["企业知识库", "模板生态", "多端预览"],
                        threats=["数据安全", "模型不稳定", "格式兼容"],
                    ),
                ),
                RoadmapSlideDSL(
                    id=new_id("slide"),
                    intent="roadmap",
                    section="路线图",
                    title="Roadmap",
                    phases=[
                        RoadmapPhase(name="MVP", timeframe="本地可跑", deliverables=["DSL v2", "RenderTree", "导出 PPTX"]),
                        RoadmapPhase(name="Editor", timeframe="前端接入", deliverables=["拖拽", "组件替换", "版本管理"]),
                        RoadmapPhase(name="Ecosystem", timeframe="插件生态", deliverables=["主题市场", "组件市场", "资产服务"]),
                    ],
                ),
                ProcessFlowSlideDSL(
                    id=new_id("slide"),
                    intent="process_flow",
                    section="流程",
                    title="Renderer Pipeline",
                    steps=[
                        ProcessStep(name="Component Planner", detail="语义→组件组合"),
                        ProcessStep(name="Layout Planner", detail="布局模板→绝对位置"),
                        ProcessStep(name="Theme Engine", detail="token→样式"),
                        ProcessStep(name="RenderTree", detail="预览 JSON"),
                        ProcessStep(name="PPT Exporter", detail="python-pptx"),
                    ],
                ),
                ChartSlideDSL(
                    id=new_id("slide"),
                    intent="chart",
                    section="数据",
                    title="示例图表",
                    chart=ChartSemantic(
                        chartType="bar",
                        labels=["Q1", "Q2", "Q3", "Q4"],
                        series=[ChartSeries(name="收入", values=[12, 18, 15, 22])],
                    ),
                ),
                ComparisonSlideDSL(
                    id=new_id("slide"),
                    intent="comparison",
                    section="对比",
                    title="AI vs Renderer 职责边界",
                    left=ComparisonSide(title="AI", bullets=["理解意图", "规划结构", "生成语义 DSL"]),
                    right=ComparisonSide(title="Renderer", bullets=["布局", "样式", "组件组合", "导出"]),
                ),
                MultiColumnSlideDSL(
                    id=new_id("slide"),
                    intent="multi_column",
                    section="扩展",
                    title="未来扩展方向",
                    columns=[
                        {"title": "模板", "bullets": ["商务/科技/学术/极简", "token 化"]},
                        {"title": "组件", "bullets": ["SWOT/Roadmap/流程图", "图表/架构图"]},
                        {"title": "服务", "bullets": ["资产服务", "导出服务", "AI 服务拆分"]},
                    ],
                ),
                ArchitectureSlideDSL(
                    id=new_id("slide"),
                    intent="architecture",
                    section="架构",
                    title="服务分层与拆分",
                    layers=[
                        {"name": "API", "items": ["FastAPI", "DTO/Schema"]},
                        {"name": "Service", "items": ["AI Pipeline", "Render Engine", "Export"]},
                        {"name": "Domain", "items": ["DSL", "RenderTree", "ThemeTokens"]},
                        {"name": "Infra", "items": ["Repo", "Assets", "MCP(可选)"]},
                    ],
                ),
                QuoteSlideDSL(
                    id=new_id("slide"),
                    intent="quote",
                    section="结束",
                    title="结语",
                    quote="LLM 负责语义，Renderer 负责视觉。",
                    author="Design Principle",
                ),
                DividerSlideDSL(
                    id=new_id("slide"),
                    intent="divider",
                    section="结束",
                    title="谢谢",
                    subtitle="Q & A",
                ),
                TeamSlideDSL(
                    id=new_id("slide"),
                    intent="team",
                    section="团队",
                    title="参与角色（示例）",
                    members=[
                        TeamMember(name="AI Agent", role="Planner", highlights=["意图分析", "DSL 生成"]),
                        TeamMember(name="Renderer", role="Engine", highlights=["布局", "主题", "组件"]),
                        TeamMember(name="Exporter", role="PPTX", highlights=["python-pptx", "格式兼容"]),
                    ],
                ),
            ],
        )

