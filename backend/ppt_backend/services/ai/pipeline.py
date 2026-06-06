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
from .client import invoke_llm_text, make_llm, parse_json, parse_model
from .schemas import IntentAnalysis, PresentationPlan


class AiPipeline:
    def __init__(self):
        self._llm = None
        self._init_error: Optional[str] = None
        try:
            self._llm = make_llm()
        except Exception as e:
            self._init_error = f"{type(e).__name__}: {e}"
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
                    "preferredTheme 只能是 modern_blue/paper_light/academic_gray/minimal_black 或 null。\n"
                    "slideCount 至少 10 页，内容丰富或含数据的主题可到 15-20 页。宁可多些页数保证内容覆盖面。",
                ),
                ("human", "{topic}"),
            ]
        )
        raw = invoke_llm_text(self._llm, prompt, {"topic": topic})
        analysis = parse_model(IntentAnalysis, raw)
        if not analysis.topic:
            analysis.topic = topic
        return analysis

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
                    "intent 必须从以下集合选择：cover/agenda/text/timeline/kpi/comparison/swot/roadmap/process_flow/chart/multi_column/architecture/quote/divider/team。\n"
                    "确保规划至少 10 页，涵盖封面、目录、多个内容页、数据页、总结/结束页。每个 section 可包含多页内容以充分展开。",
                ),
                ("human", "{analysis_json}"),
            ]
        )
        raw = invoke_llm_text(self._llm, prompt, {"analysis_json": analysis.model_dump_json(by_alias=True)})
        plan = parse_model(PresentationPlan, raw)
        if not plan.title:
            plan.title = analysis.topic
        return plan

    def generate_dsl(self, topic: str, theme: Optional[str] = None, rag_context: str = "") -> PresentationDSL:
        dsl, _ = self.generate_dsl_with_debug(topic=topic, theme=theme, rag_context=rag_context)
        return dsl

    def generate_dsl_with_debug(self, topic: str, theme: Optional[str] = None, rag_context: str = ""):
        if not topic:
            raise ValueError("topic required")

        if not self._llm:
            return (
                self._fallback(topic, theme),
                {
                    "llmConfigured": False,
                    "usedFallback": True,
                    "stage": "init",
                    "error": self._init_error or "LLM not configured",
                },
            )

        try:
            analysis = self.analyze_intent(topic)
            plan = self.plan_presentation(analysis)
        except Exception as e:
            return (
                self._fallback(topic, theme),
                {
                    "llmConfigured": True,
                    "usedFallback": True,
                    "stage": "analyze_or_plan",
                    "error": f"{type(e).__name__}: {e}",
                },
            )

        theme_name = theme or plan.theme or analysis.preferred_theme or "modern_blue"
        _ = get_theme_tokens(theme_name)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是 PPT DSL Generator。你只输出 JSON，不要输出任何解释文字。\n"
                    "你必须输出 PresentationDSL：包含 title/audience/tone/theme/slides。\n"
                    "slides 是语义化页面 DSL，使用 intent 作为 discriminant。\n"
                    '''
                    所有 slide 必须严格包含：
                    {{
                    "id": "slide_xxx",
                    "intent": "...",
                    "section": "...",
                    "title": "...",
                    "notes": []
                    }}

                    注意：
                    - id 必须存在且是 string
                    - notes 必须是 string array
                    - 即使只有一条 note，也必须：
                    "notes": ["xxx"]
                    - 禁止：
                    "notes": "xxx"

                    ## 例子：
                    {{
                        "id": "slide_cover",
                        "intent": "cover",
                        "section": "封面",
                        "title": "软件工程导论",
                        "notes": [
                            "建立主题认知",
                            "展示课程目标"
                        ],
                        "subtitle": "Software Engineering"
                    }}\n
                    '''
                    "字段类型必须严格匹配：\n"
                    "- cover: subtitle/tagline/highlights(list[str])\n"
                    "- agenda: items(list[str])，不要输出对象数组\n"
                    "- text: paragraphs(list[str]) / bullets(list[str])\n"
                    "- timeline: events(list[object])，每个 event 至少有 label，可选 date/detail\n"
                    "- kpi: items(list[object])，每个 item 有 label/value，可选 unit/delta\n"
                    "- comparison: left/right(object) 各含 title(str)/bullets(list[str])\n"
                    "- swot: swot(object) 含 strengths/weaknesses/opportunities/threats(list[str])\n"
                    "- roadmap: phases(list[object]) 含 name/timeframe/deliverables(list[str])\n"
                    "- process_flow: steps(list[object]) 含 name/detail\n"
                    "- chart: chart(object) 含 chartType(bar|line|pie)/labels(list[str])/series(list[object])，其中每个 series 对象包含 name 与 values(list[number])\n"
                    "- multi_column: columns(list[object]) 含 title/bullets(list[str])\n"
                    "- architecture: layers(list[object]) 含 name/items(list[str])\n"
                    "- quote: quote(str)/author(str|null)\n"
                    "- divider: subtitle(str|null)\n"
                    "- team: members(list[object]) 含 name/role/highlights(list[str])\n"
                    "严格禁止输出任何布局字段：x/y/w/h/fontSize/templateId/坐标/尺寸。\n"
                    "只输出结构化语义数据（如 items/events/phases/steps/columns/layers 等）。\n\n"
                    "## 内容丰富度要求（重要）：\n"
                    "当《提供了》参考资料(RAG)时（rag_block 非空）：\n"
                    "- 每页 text slide 的 bullets 至少 4-6 条，每条用完整的句子表达，包含具体信息\n"
                    "- 每页 text slide 的 paragraphs 至少 1-2 段，每段 2-3 句充实内容\n"
                    "- 必须从参考资料中提取具体数据、案例、趋势、事实融入内容\n"
                    "- KPI 页至少包含 3-4 个指标，附带具体数值\n"
                    "- Timeline 页至少包含 4-6 个事件，每个事件有详细说明\n"
                    "- Roadmap 页每个 phase 至少包含 2-4 个 deliverables\n"
                    "- 每个 section 应包含足够的 slides 来充分展开主题\n\n"
                    "当《没有提供》参考资料（rag_block 为空）时：\n"
                    "- 内容保持简洁精炼，每页 text slide 的 bullets 只需 2-3 条\n"
                    "- 每页 text slide 的 paragraphs 只需 0-1 段简短内容\n"
                    "- KPI 页只需 2 个指标，Timeline 只需 2-3 个事件\n"
                    "- Roadmap 每个 phase 只需 1-2 个 deliverables\n"
                    "- 避免冗长，只保留最核心的信息点\n"
                    "- 总页数可适当减少至 8-10 页\n\n"
                    "通用规则（始终遵守）：\n"
                    "- 避免低信息量内容如单独一个\"概述\"、\"简介\"等空洞短语",
                ),
                ("human", "topic: {topic}\nanalysis: {analysis_json}\nplan: {plan_json}\ntheme: {theme_name}\n{rag_block}"),
            ]
        )
        try:
            rag_block = ""
            if rag_context:
                rag_block = (
                    f"\n## 参考资料（来自知识库和网络搜索，务必充分利用）\n"
                    f"请大量引用以下资料中的具体数据、案例、趋势、事实来丰富 PPT 内容。"
                    f"每页内容应从参考资料中提取相关信息，而非泛泛而谈。\n{rag_context}\n"
                    f"基于以上参考资料，确保生成的内容有深度、有数据支撑、有具体案例。"
                )

            raw = invoke_llm_text(
                self._llm,
                prompt,
                {
                    "topic": topic,
                    "analysis_json": analysis.model_dump_json(by_alias=True),
                    "plan_json": plan.model_dump_json(),
                    "theme_name": theme_name,
                    "rag_block": rag_block,
                },
            )
        except Exception as e:
            return (
                self._fallback(topic, theme_name),
                {
                    "llmConfigured": True,
                    "usedFallback": True,
                    "stage": "dsl_invoke",
                    "error": f"{type(e).__name__}: {e}",
                },
            )
        try:
            dsl = parse_model(PresentationDSL, raw)
        except Exception as e:
            try:
                data = parse_json(raw)
                repaired = self._repair_dsl_dict(data, topic=topic, analysis=analysis, theme_name=theme_name)
                dsl = PresentationDSL.model_validate(repaired)
                dsl.theme = theme_name
                if not dsl.title:
                    dsl.title = plan.title or topic
                return (
                    dsl,
                    {
                        "llmConfigured": True,
                        "usedFallback": False,
                        "stage": "dsl_repair",
                        "error": f"{type(e).__name__}: {e}",
                    },
                )
            except Exception as e2:
                return (
                    self._fallback(topic, theme_name),
                    {
                        "llmConfigured": True,
                        "usedFallback": True,
                        "stage": "dsl_parse",
                        "error": f"{type(e).__name__}: {e} | repair_failed: {type(e2).__name__}: {e2}",
                    },
                )
        dsl.theme = theme_name
        if not dsl.title:
            dsl.title = plan.title or topic
        if not dsl.slides:
            return (
                self._fallback(topic, theme_name),
                {
                    "llmConfigured": True,
                    "usedFallback": True,
                    "stage": "dsl_empty",
                    "error": "empty slides",
                },
            )
        return (
            dsl,
            {
                "llmConfigured": True,
                "usedFallback": False,
                "stage": "ok",
                "error": None,
            },
        )

    def _repair_dsl_dict(self, data: dict, *, topic: str, analysis: IntentAnalysis, theme_name: str) -> dict:
        title = data.get("title") or topic
        audience = data.get("audience") or analysis.audience or "通用受众"
        tone = data.get("tone") or analysis.tone or "清晰、教学"

        slides_in = data.get("slides")
        if not isinstance(slides_in, list):
            slides_in = []

        slides_out = []
        for s in slides_in:
            if not isinstance(s, dict):
                continue
            slides_out.append(self._repair_slide_dict(s, topic=title))

        if not slides_out:
            return {
                "title": title,
                "audience": audience,
                "tone": tone,
                "theme": theme_name,
                "slides": [],
            }

        return {
            "title": title,
            "audience": audience,
            "tone": tone,
            "theme": theme_name,
            "slides": slides_out,
        }

    def _repair_slide_dict(self, s: dict, *, topic: str) -> dict:
        allowed_intents = {
            "cover",
            "agenda",
            "text",
            "timeline",
            "kpi",
            "comparison",
            "swot",
            "roadmap",
            "process_flow",
            "chart",
            "multi_column",
            "architecture",
            "quote",
            "divider",
            "team",
        }

        def as_str(v) -> str:
            if v is None:
                return ""
            if isinstance(v, str):
                return v
            return str(v)

        def as_str_list(v):
            if v is None:
                return []
            if isinstance(v, str):
                txt = v.strip()
                return [txt] if txt else []
            if isinstance(v, list):
                out = []
                for it in v:
                    if it is None:
                        continue
                    if isinstance(it, str):
                        t = it.strip()
                        if t:
                            out.append(t)
                        continue
                    if isinstance(it, dict):
                        for k in ("label", "title", "name", "text", "content"):
                            if isinstance(it.get(k), str) and it.get(k).strip():
                                out.append(it.get(k).strip())
                                break
                        continue
                    out.append(str(it))
                return out
            if isinstance(v, dict):
                for k in ("items", "bullets", "highlights", "paragraphs", "texts"):
                    if k in v:
                        return as_str_list(v.get(k))
                for k in ("label", "title", "name", "text", "content"):
                    if isinstance(v.get(k), str) and v.get(k).strip():
                        return [v.get(k).strip()]
                return []
            return [str(v)]

        def pick_slide_intent(slide_dict: dict) -> str:
            v = slide_dict.get("intent")
            if isinstance(v, str) and v in allowed_intents:
                return v
            for k in allowed_intents:
                if isinstance(slide_dict.get(k), dict):
                    return k
            return as_str(v)

        intent = pick_slide_intent(s)
        wrapper = s.get(intent) if isinstance(s.get(intent), dict) else {}
        if not isinstance(wrapper, dict):
            wrapper = {}

        slide_id = s.get("id") or wrapper.get("id") or new_id("slide")
        section = s.get("section") or wrapper.get("section") or ""
        title = s.get("title") or wrapper.get("title") or topic
        notes_raw = s.get("notes") if s.get("notes") is not None else wrapper.get("notes")
        base = {
            "id": as_str(slide_id) or new_id("slide"),
            "intent": intent if intent in allowed_intents else "text",
            "section": as_str(section),
            "title": as_str(title) or topic,
            "notes": as_str_list(notes_raw),
        }

        if intent == "cover":
            return {
                **base,
                "subtitle": as_str(s.get("subtitle") if s.get("subtitle") is not None else wrapper.get("subtitle")) or None,
                "tagline": as_str(s.get("tagline") if s.get("tagline") is not None else wrapper.get("tagline")) or None,
                "highlights": as_str_list(s.get("highlights") if s.get("highlights") is not None else wrapper.get("highlights")),
            }

        if intent == "agenda":
            items_raw = s.get("items") if s.get("items") is not None else wrapper.get("items")
            return {**base, "items": as_str_list(items_raw)}

        if intent == "text":
            content = s.get("content") or wrapper.get("content")
            paragraphs_raw = s.get("paragraphs") if s.get("paragraphs") is not None else wrapper.get("paragraphs")
            bullets_raw = s.get("bullets") if s.get("bullets") is not None else wrapper.get("bullets")
            paragraphs = as_str_list(paragraphs_raw)
            bullets = as_str_list(bullets_raw)
            if (not paragraphs) and (not bullets) and isinstance(content, str) and content.strip():
                paragraphs = [content.strip()]
            if (not paragraphs) and isinstance(content, dict):
                paragraphs = as_str_list(content.get("paragraphs") or content.get("content") or content.get("text"))
                if not bullets:
                    bullets = as_str_list(content.get("bullets") or content.get("items"))
            return {
                **base,
                "paragraphs": paragraphs,
                "bullets": bullets,
            }

        if intent == "timeline":
            events_raw = s.get("events") if s.get("events") is not None else wrapper.get("events")
            events_out = []
            if isinstance(events_raw, list):
                for it in events_raw:
                    if it is None:
                        continue
                    if isinstance(it, str):
                        txt = it.strip()
                        if txt:
                            events_out.append({"label": txt})
                        continue
                    if isinstance(it, dict):
                        label = it.get("label") or it.get("title") or it.get("name") or it.get("event")
                        if not isinstance(label, str) or not label.strip():
                            continue
                        date = it.get("date") or it.get("time") or it.get("when")
                        detail = it.get("detail") or it.get("desc") or it.get("description") or it.get("content")
                        ev = {"label": label.strip()}
                        if isinstance(date, str) and date.strip():
                            ev["date"] = date.strip()
                        if isinstance(detail, str) and detail.strip():
                            ev["detail"] = detail.strip()
                        events_out.append(ev)
                        continue
            return {**base, "events": events_out}

        if intent == "kpi":
            items_raw = s.get("items") if s.get("items") is not None else wrapper.get("items")
            items_out = []
            if isinstance(items_raw, list):
                for it in items_raw:
                    if it is None:
                        continue
                    if isinstance(it, str):
                        txt = it.strip()
                        if not txt:
                            continue
                        if "：" in txt:
                            k, v = txt.split("：", 1)
                            items_out.append({"label": k.strip() or txt, "value": v.strip() or ""})
                        elif ":" in txt:
                            k, v = txt.split(":", 1)
                            items_out.append({"label": k.strip() or txt, "value": v.strip() or ""})
                        else:
                            items_out.append({"label": txt, "value": ""})
                        continue
                    if isinstance(it, dict):
                        label = it.get("label") or it.get("name") or it.get("title")
                        value = it.get("value") or it.get("val") or it.get("number")
                        unit = it.get("unit")
                        delta = it.get("delta") or it.get("change")
                        item = {"label": as_str(label) or "指标", "value": as_str(value)}
                        if isinstance(unit, str) and unit.strip():
                            item["unit"] = unit.strip()
                        if isinstance(delta, str) and delta.strip():
                            item["delta"] = delta.strip()
                        items_out.append(item)
                        continue
            return {**base, "items": items_out}

        if intent == "comparison":
            left = s.get("left") or wrapper.get("left") or {"title": "左", "bullets": []}
            right = s.get("right") or wrapper.get("right") or {"title": "右", "bullets": []}
            if isinstance(left, list):
                left = {"title": "左", "bullets": as_str_list(left)}
            if isinstance(right, list):
                right = {"title": "右", "bullets": as_str_list(right)}
            if isinstance(left, dict):
                left = {"title": as_str(left.get("title") or left.get("name") or "左"), "bullets": as_str_list(left.get("bullets") or left.get("items"))}
            else:
                left = {"title": "左", "bullets": []}
            if isinstance(right, dict):
                right = {"title": as_str(right.get("title") or right.get("name") or "右"), "bullets": as_str_list(right.get("bullets") or right.get("items"))}
            else:
                right = {"title": "右", "bullets": []}
            return {**base, "left": left, "right": right}

        if intent == "swot":
            swot = s.get("swot") or wrapper.get("swot") or {
                "strengths": s.get("strengths") or [],
                "weaknesses": s.get("weaknesses") or [],
                "opportunities": s.get("opportunities") or [],
                "threats": s.get("threats") or [],
            }
            if not isinstance(swot, dict):
                swot = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
            swot = {
                "strengths": as_str_list(swot.get("strengths") or swot.get("s")),
                "weaknesses": as_str_list(swot.get("weaknesses") or swot.get("w")),
                "opportunities": as_str_list(swot.get("opportunities") or swot.get("o")),
                "threats": as_str_list(swot.get("threats") or swot.get("t")),
            }
            return {**base, "swot": swot}

        if intent == "roadmap":
            phases_raw = s.get("phases") if s.get("phases") is not None else wrapper.get("phases")
            phases_out = []
            if isinstance(phases_raw, list):
                for it in phases_raw:
                    if it is None:
                        continue
                    if isinstance(it, str):
                        txt = it.strip()
                        if txt:
                            phases_out.append({"name": txt, "deliverables": []})
                        continue
                    if isinstance(it, dict):
                        name = it.get("name") or it.get("phase") or it.get("title") or it.get("label")
                        timeframe = it.get("timeframe") or it.get("time") or it.get("when") or it.get("period")
                        deliverables = it.get("deliverables") or it.get("tasks") or it.get("items") or it.get("outputs")
                        phases_out.append(
                            {
                                "name": as_str(name) or "阶段",
                                "timeframe": as_str(timeframe) or None,
                                "deliverables": as_str_list(deliverables),
                            }
                        )
                        continue
            return {**base, "phases": phases_out}

        if intent == "process_flow":
            raw_steps = (s.get("steps") or wrapper.get("steps") or [])
            steps = []
            if isinstance(raw_steps, list):
                for it in raw_steps:
                    if isinstance(it, dict):
                        name = it.get("name") or it.get("label") or it.get("title") or it.get("step")
                        detail = it.get("detail") or it.get("desc") or it.get("description") or it.get("content")
                        steps.append({"name": as_str(name) or "步骤", "detail": as_str(detail) or None})
                        continue
                    if isinstance(it, str):
                        txt = it.strip()
                        if "：" in txt:
                            n, d = txt.split("：", 1)
                            steps.append({"name": n.strip(), "detail": d.strip()})
                        elif ":" in txt:
                            n, d = txt.split(":", 1)
                            steps.append({"name": n.strip(), "detail": d.strip()})
                        else:
                            steps.append({"name": txt, "detail": None})
            return {**base, "steps": steps}

        if intent == "chart":
            chart = s.get("chart") or wrapper.get("chart") or wrapper
            if not isinstance(chart, dict):
                chart = {}
            chart_type = chart.get("chartType") or chart.get("chart_type") or chart.get("type") or "bar"
            if chart_type not in ("bar", "line", "pie"):
                chart_type = "bar"
            labels = as_str_list(chart.get("labels") or chart.get("x") or chart.get("categories"))
            series_raw = chart.get("series") or chart.get("data") or []
            series_out = []
            if isinstance(series_raw, list):
                for it in series_raw:
                    if it is None:
                        continue
                    if isinstance(it, dict):
                        name = it.get("name") or it.get("label") or it.get("title") or "Series"
                        values_raw = it.get("values") or it.get("data") or []
                        values_out = []
                        if isinstance(values_raw, list):
                            for vv in values_raw:
                                if isinstance(vv, (int, float)):
                                    values_out.append(float(vv))
                                elif isinstance(vv, str):
                                    try:
                                        values_out.append(float(vv.strip()))
                                    except Exception:
                                        continue
                        series_out.append({"name": as_str(name) or "Series", "values": values_out})
                        continue
            return {
                **base,
                "chart": {
                    "chartType": chart_type,
                    "labels": labels,
                    "series": series_out,
                },
            }

        if intent == "multi_column":
            cols_raw = s.get("columns") if s.get("columns") is not None else wrapper.get("columns")
            cols_out = []
            if isinstance(cols_raw, list):
                for it in cols_raw:
                    if it is None:
                        continue
                    if isinstance(it, str):
                        txt = it.strip()
                        if txt:
                            cols_out.append({"title": txt, "bullets": []})
                        continue
                    if isinstance(it, dict):
                        col_title = it.get("title") or it.get("name") or it.get("label")
                        bullets = it.get("bullets") or it.get("items") or it.get("points") or it.get("highlights")
                        cols_out.append({"title": as_str(col_title) or "要点", "bullets": as_str_list(bullets)})
                        continue
            return {**base, "columns": cols_out}

        if intent == "architecture":
            layers_raw = s.get("layers") if s.get("layers") is not None else wrapper.get("layers")
            layers_out = []
            if isinstance(layers_raw, list):
                for it in layers_raw:
                    if it is None:
                        continue
                    if isinstance(it, str):
                        txt = it.strip()
                        if txt:
                            layers_out.append({"name": txt, "items": []})
                        continue
                    if isinstance(it, dict):
                        name = it.get("name") or it.get("layer") or it.get("title") or it.get("label")
                        items = it.get("items") or it.get("bullets") or it.get("components") or it.get("modules")
                        layers_out.append({"name": as_str(name) or "层", "items": as_str_list(items)})
                        continue
            return {**base, "layers": layers_out}

        if intent == "quote":
            quote = s.get("quote") or wrapper.get("quote") or s.get("text") or base["title"]
            author = s.get("author") if s.get("author") is not None else wrapper.get("author")
            return {**base, "quote": as_str(quote) or base["title"], "author": as_str(author) or None}

        if intent == "divider":
            subtitle = s.get("subtitle") if s.get("subtitle") is not None else wrapper.get("subtitle")
            return {**base, "subtitle": as_str(subtitle) or None}

        if intent == "team":
            members_raw = s.get("members") if s.get("members") is not None else wrapper.get("members")
            members_out = []
            if isinstance(members_raw, list):
                for it in members_raw:
                    if it is None:
                        continue
                    if isinstance(it, str):
                        txt = it.strip()
                        if txt:
                            members_out.append({"name": txt, "highlights": []})
                        continue
                    if isinstance(it, dict):
                        name = it.get("name") or it.get("title") or it.get("label")
                        role = it.get("role") or it.get("position")
                        highlights = it.get("highlights") or it.get("bullets") or it.get("items") or it.get("points")
                        members_out.append(
                            {
                                "name": as_str(name) or "成员",
                                "role": as_str(role) or None,
                                "highlights": as_str_list(highlights),
                            }
                        )
                        continue
            return {**base, "members": members_out}

        return {**base, "intent": "text", "paragraphs": [], "bullets": [base["title"]]}

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

