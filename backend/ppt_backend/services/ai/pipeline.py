from __future__ import annotations

from typing import Any, Optional

from ...domain.dsl import (
    ArchitectureLayer,
    ChartSemantic,
    ChartSeries,
    ColumnBlock,
    ComparisonSide,
    KPIItem,
    PresentationDSL,
    ProcessStep,
    RoadmapPhase,
    SwotBlock,
    TeamMember,
    TimelineEvent,
)
from ...domain.ids import new_id
from ...domain.theme import get_theme_tokens
from .client import invoke_llm_text, make_llm, parse_json, parse_model
from .model_config import UserLLMConfig
from .prompts import dsl_generation_prompt, intent_analysis_prompt, presentation_plan_prompt
from .schemas import IntentAnalysis, PresentationPlan


class AiPipeline:
    def __init__(self, llm_config: Optional[UserLLMConfig] = None, model_provider: Optional[str] = None):
        self._llm = None
        self._init_error: Optional[str] = None
        try:
            if llm_config is None and model_provider:
                llm_config = UserLLMConfig(provider=model_provider)
            self._llm = make_llm(llm_config)
        except Exception as e:
            self._init_error = f"{type(e).__name__}: {e}"
            self._llm = None

    def analyze_intent(self, topic: str, target_slide_count: int = 14, page_count_preset: str = "medium") -> IntentAnalysis:
        if not self._llm:
            raise RuntimeError("LLM not configured")
        raw = invoke_llm_text(
            self._llm,
            intent_analysis_prompt(),
            {
                "topic": topic,
                "target_slide_count": target_slide_count,
                "page_count_preset": page_count_preset,
            },
        )
        analysis = parse_model(IntentAnalysis, raw)
        analysis.slide_count = target_slide_count
        if not analysis.topic:
            analysis.topic = topic
        return analysis

    def plan_presentation(self, analysis: IntentAnalysis) -> PresentationPlan:
        if not self._llm:
            raise RuntimeError("LLM not configured")
        raw = invoke_llm_text(
            self._llm,
            presentation_plan_prompt(),
            {"analysis_json": analysis.model_dump_json(by_alias=True)},
        )
        plan = parse_model(PresentationPlan, raw)
        if not plan.title:
            plan.title = analysis.topic
        return plan

    def generate_dsl(
        self,
        topic: str,
        theme: Optional[str] = None,
        rag_context: str = "",
        target_slide_count: int = 14,
        page_count_preset: str = "medium",
    ) -> PresentationDSL:
        dsl, _ = self.generate_dsl_with_debug(
            topic=topic,
            theme=theme,
            rag_context=rag_context,
            target_slide_count=target_slide_count,
            page_count_preset=page_count_preset,
        )
        return dsl

    def generate_dsl_with_debug(
        self,
        topic: str,
        theme: Optional[str] = None,
        rag_context: str = "",
        target_slide_count: int = 14,
        page_count_preset: str = "medium",
    ):
        if not topic:
            raise ValueError("topic required")
        if not self._llm:
            raise RuntimeError(self._init_error or "LLM not configured")

        try:
            analysis = self.analyze_intent(
                topic,
                target_slide_count=target_slide_count,
                page_count_preset=page_count_preset,
            )
            plan = self.plan_presentation(analysis)
        except Exception as e:
            raise RuntimeError(f"AI analyze/plan failed: {type(e).__name__}: {e}") from e

        theme_name = theme or "paper_light"
        _ = get_theme_tokens(theme_name)

        try:
            rag_block = ""
            if rag_context:
                rag_block = "\n## Reference material\n" + rag_context + "\n"
            raw = invoke_llm_text(
                self._llm,
                dsl_generation_prompt(),
                {
                    "topic": topic,
                    "target_slide_count": target_slide_count,
                    "analysis_json": analysis.model_dump_json(by_alias=True),
                    "plan_json": plan.model_dump_json(),
                    "theme_name": theme_name,
                    "rag_block": rag_block,
                },
            )
        except Exception as e:
            raise RuntimeError(f"AI DSL generation failed: {type(e).__name__}: {e}") from e

        try:
            dsl = parse_model(PresentationDSL, raw)
        except Exception as e:
            try:
                data = parse_json(raw)
                repaired = self._repair_dsl_dict(data, topic=topic, analysis=analysis, theme_name=theme_name)
                dsl = PresentationDSL.model_validate(repaired)
                dsl = self._normalize_generated_dsl(dsl)
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
                raise ValueError(
                    f"AI DSL parse failed: {type(e).__name__}: {e} | repair_failed: {type(e2).__name__}: {e2}"
                ) from e2

        dsl.theme = theme_name
        if not dsl.title:
            dsl.title = plan.title or topic
        dsl = self._normalize_generated_dsl(dsl)
        if not dsl.slides:
            raise ValueError("AI DSL generation produced empty slides")
        return (
            dsl,
            {
                "llmConfigured": True,
                "usedFallback": False,
                "stage": "ok",
                "error": None,
            },
        )

    def _normalize_generated_dsl(self, dsl: PresentationDSL) -> PresentationDSL:
        def clean_list(values):
            return [v.strip() for v in (values or []) if isinstance(v, str) and v.strip()]

        def ensure_notes(slide, text):
            notes = clean_list(getattr(slide, "notes", []) or [])
            slide.notes = notes or [text]

        def defaults(title, count=3):
            base = title or "content"
            samples = [
                f"Explain the core concept and use scenario of {base}",
                f"Analyze key problems, methods, and constraints of {base}",
                f"Summarize the value of {base} for the whole topic",
                f"Provide practical implementation points for {base}",
                f"Identify risks and improvement directions for {base}",
            ]
            return samples[:count]

        for slide in dsl.slides:
            intent = getattr(slide, "intent", "")
            title = getattr(slide, "title", "") or "content"
            ensure_notes(slide, f"This slide explains {title} and its role in the outline.")

            if intent == "cover":
                if not getattr(slide, "subtitle", None) and not getattr(slide, "tagline", None):
                    slide.subtitle = "Core concepts, methods, and practical value"
                highlights = clean_list(getattr(slide, "highlights", []) or [])
                while len(highlights) < 3:
                    highlights.append(defaults(title, 5)[len(highlights)])
                slide.highlights = highlights[:5]
                continue

            if intent == "agenda":
                items = clean_list(getattr(slide, "items", []) or [])
                if len(items) < 5:
                    items = ["Background", "Core concepts", "Key methods", "Process", "Cases and summary"]
                slide.items = items[:8]
                continue

            if intent == "text":
                paragraphs = clean_list(getattr(slide, "paragraphs", []) or [])
                bullets = clean_list(getattr(slide, "bullets", []) or [])
                if not paragraphs:
                    head = ", ".join((bullets or defaults(title, 3))[:2])
                    paragraphs = [
                        f"{title} should be explained from background, problems, and methods. Around {head}, the audience can build a clear knowledge framework and connect concepts to practical scenarios."
                    ]
                while len(bullets) < 3:
                    bullets.append(defaults(title, 5)[len(bullets)])
                slide.paragraphs = paragraphs[:2]
                slide.bullets = bullets[:5]
                continue

            if intent == "timeline":
                events = list(getattr(slide, "events", []) or [])
                while len(events) < 4:
                    idx = len(events) + 1
                    events.append(TimelineEvent(label=f"Stage {idx}", date=f"Stage {idx}", detail=f"Explain key tasks, outputs, and evolution meaning for {title}."))
                slide.events = events[:6]
                continue

            if intent == "kpi":
                items = list(getattr(slide, "items", []) or [])
                fallback = [("Coverage", "80", "%", "Scope coverage"), ("Efficiency", "30", "%", "Improvement potential"), ("Quality", "90", "%", "Result stability")]
                while len(items) < 3:
                    label, value, unit, delta = fallback[len(items) % len(fallback)]
                    items.append(KPIItem(label=label, value=value, unit=unit, delta=delta))
                slide.items = items[:5]
                continue

            if intent == "comparison":
                left = getattr(slide, "left", None) or ComparisonSide(title="Option A", bullets=[])
                right = getattr(slide, "right", None) or ComparisonSide(title="Option B", bullets=[])
                if not getattr(left, "title", "") or left.title == "Left":
                    left.title = "Option A"
                if not getattr(right, "title", "") or right.title == "Right":
                    right.title = "Option B"
                left_bullets = clean_list(getattr(left, "bullets", []) or [])
                right_bullets = clean_list(getattr(right, "bullets", []) or [])
                while len(left_bullets) < 3:
                    left_bullets.append(f"Explain {left.title} by goal, cost, or scenario")
                while len(right_bullets) < 3:
                    right_bullets.append(f"Explain {right.title} by goal, cost, or scenario")
                left.bullets = left_bullets[:5]
                right.bullets = right_bullets[:5]
                slide.left = left
                slide.right = right
                continue

            if intent == "swot":
                swot = getattr(slide, "swot", None) or SwotBlock()
                for attr, label in (("strengths", "strength"), ("weaknesses", "weakness"), ("opportunities", "opportunity"), ("threats", "threat")):
                    values = clean_list(getattr(swot, attr, []) or [])
                    while len(values) < 2:
                        values.append(f"Analyze one key {label} related to {title}")
                    setattr(swot, attr, values[:4])
                slide.swot = swot
                continue

            if intent == "roadmap":
                phases = list(getattr(slide, "phases", []) or [])
                while len(phases) < 3:
                    idx = len(phases) + 1
                    phases.append(RoadmapPhase(name=f"Phase {idx}", timeframe=f"Phase {idx}", deliverables=[f"Complete tasks related to {title}", "Create verifiable outputs"]))
                for phase in phases:
                    deliverables = clean_list(getattr(phase, "deliverables", []) or [])
                    while len(deliverables) < 2:
                        deliverables.append(f"Add a key deliverable for {phase.name}")
                    phase.deliverables = deliverables[:4]
                slide.phases = phases[:5]
                continue

            if intent == "process_flow":
                steps = list(getattr(slide, "steps", []) or [])
                while len(steps) < 4:
                    idx = len(steps) + 1
                    steps.append(ProcessStep(name=f"Step {idx}", detail=f"Explain input, action, and output for {title}."))
                slide.steps = steps[:7]
                continue

            if intent == "chart":
                chart = getattr(slide, "chart", None)
                if not chart:
                    chart = ChartSemantic(chartType="bar", labels=["A", "B", "C", "D"], series=[ChartSeries(name="Example", values=[20, 35, 50, 65])])
                labels = clean_list(getattr(chart, "labels", []) or [])
                if len(labels) < 4:
                    labels = ["A", "B", "C", "D"]
                series = list(getattr(chart, "series", []) or []) or [ChartSeries(name="Example", values=[20, 35, 50, 65])]
                for item in series:
                    values = list(getattr(item, "values", []) or [])
                    while len(values) < len(labels):
                        values.append(float(10 + len(values) * 10))
                    item.values = values[:len(labels)]
                chart.labels = labels[:6]
                chart.series = series[:3]
                slide.chart = chart
                continue

            if intent == "multi_column":
                columns = list(getattr(slide, "columns", []) or [])
                while len(columns) < 2:
                    idx = len(columns) + 1
                    columns.append(ColumnBlock(title=f"Dimension {idx}", bullets=defaults(title, 3)))
                for col in columns:
                    bullets = clean_list(getattr(col, "bullets", []) or [])
                    while len(bullets) < 3:
                        bullets.append(defaults(title, 5)[len(bullets)])
                    col.bullets = bullets[:5]
                slide.columns = columns[:4]
                continue

            if intent == "architecture":
                layers = list(getattr(slide, "layers", []) or [])
                while len(layers) < 3:
                    idx = len(layers) + 1
                    layers.append(ArchitectureLayer(name=f"Layer {idx}", items=defaults(title, 3)))
                for layer in layers:
                    items = clean_list(getattr(layer, "items", []) or [])
                    while len(items) < 2:
                        items.append(f"Add component for {title}")
                    layer.items = items[:5]
                slide.layers = layers[:5]
                continue

            if intent == "quote":
                if not getattr(slide, "quote", ""):
                    slide.quote = f"{title} is valuable because it guides analysis and improvement of real problems."
                if not getattr(slide, "author", None):
                    slide.author = "Course summary"
                continue

            if intent == "divider":
                if not getattr(slide, "subtitle", None):
                    slide.subtitle = f"Next section: {title}."
                continue

            if intent == "team":
                members = list(getattr(slide, "members", []) or [])
                while len(members) < 3:
                    idx = len(members) + 1
                    members.append(TeamMember(name=f"Role {idx}", role="Key participant", highlights=defaults(title, 3)))
                for member in members:
                    highlights = clean_list(getattr(member, "highlights", []) or [])
                    while len(highlights) < 2:
                        highlights.append(f"Explain this role's responsibility in {title}")
                    member.highlights = highlights[:4]
                slide.members = members[:6]
                continue
        return dsl

    def _repair_dsl_dict(self, data: dict, *, topic: str, analysis: IntentAnalysis, theme_name: str) -> dict:
        def as_str(v: Any) -> str:
            if v is None:
                return ""
            if isinstance(v, str):
                return v.strip()
            if isinstance(v, list):
                return " / ".join(as_str(item) for item in v if as_str(item))
            if isinstance(v, dict):
                for key in ("label", "title", "name", "text", "content", "value"):
                    value = v.get(key)
                    if value is not None:
                        text = as_str(value)
                        if text:
                            return text
                return " / ".join(as_str(value) for value in v.values() if as_str(value))
            return str(v)

        if not isinstance(data, dict):
            data = {}

        title = as_str(data.get("title")) or topic
        audience = as_str(data.get("audience")) or as_str(analysis.audience) or "General audience"
        tone = as_str(data.get("tone")) or as_str(analysis.tone) or "Clear and professional"

        slides_in = data.get("slides")
        if not isinstance(slides_in, list):
            slides_in = []

        slides_out = []
        for s in slides_in:
            if isinstance(s, dict):
                slides_out.append(self._repair_slide_dict(s, topic=title))
        slides_out = self._rebalance_slide_intents(slides_out, topic=title, target_count=analysis.slide_count)

        return {
            "title": title,
            "audience": audience,
            "tone": tone,
            "theme": theme_name,
            "slides": slides_out,
        }

    def _rebalance_slide_intents(self, slides: list[dict], *, topic: str, target_count: int) -> list[dict]:
        return slides

    def _coerce_slide_intent(self, slide: dict, *, intent: str, topic: str, index: int) -> dict:
        def text(value: Any) -> str:
            if value is None:
                return ""
            if isinstance(value, str):
                return value.strip()
            if isinstance(value, dict):
                label = text(value.get("label") or value.get("title") or value.get("name") or value.get("text") or value.get("content"))
                raw_value = text(value.get("value") if value.get("value") is not None else value.get("number"))
                unit = text(value.get("unit"))
                detail = text(value.get("detail") or value.get("desc") or value.get("description") or value.get("delta"))
                parts = []
                if label:
                    parts.append(label)
                if raw_value:
                    parts.append(f"{raw_value}{unit}")
                if detail:
                    parts.append(detail)
                if parts:
                    return " - ".join(parts)
                return " / ".join(text(v) for v in value.values() if text(v))
            if isinstance(value, list):
                return " / ".join(text(v) for v in value if text(v))
            return str(value).strip()

        def text_list(value: Any) -> list[str]:
            if value is None:
                return []
            if isinstance(value, list):
                return [item for item in (text(v) for v in value) if item]
            item = text(value)
            return [item] if item else []

        def first_list(*values: Any) -> list[str]:
            for value in values:
                items = text_list(value)
                if items:
                    return items
            return []

        title = text(slide.get("title")) or topic
        section = text(slide.get("section"))
        notes = first_list(slide.get("notes"), slide.get("purpose"), slide.get("intent"))
        if not notes:
            notes = [f"Explain the role of {title} in {topic}."]
        bullets = first_list(slide.get("bullets"), slide.get("items"), slide.get("highlights"), slide.get("points"))
        paragraphs = first_list(slide.get("paragraphs"), slide.get("content"), slide.get("summary"), slide.get("description"))
        if not bullets and paragraphs:
            bullets = paragraphs[:3]
        if not bullets:
            bullets = [f"Key point for {title}", f"Evidence or context for {title}", f"Implication for {topic}"]

        base = {
            "id": text(slide.get("id")) or new_id("slide"),
            "intent": intent,
            "section": section,
            "title": title,
            "notes": notes,
        }

        if intent == "cover":
            return {
                **base,
                "title": topic,
                "subtitle": text(slide.get("subtitle")) or title,
                "tagline": text(slide.get("tagline")) or None,
                "highlights": bullets[:3],
            }
        if intent == "agenda":
            return {**base, "items": bullets[:8]}
        if intent == "multi_column":
            columns = []
            for item in slide.get("columns") or []:
                if isinstance(item, dict):
                    columns.append({"title": text(item.get("title") or item.get("name") or item.get("label")) or title, "bullets": first_list(item.get("bullets"), item.get("items"), item.get("points")) or bullets[:3]})
            return {
                **base,
                "columns": columns or [
                    {"title": title, "bullets": bullets[:3]},
                    {"title": f"{title} details", "bullets": (bullets[3:6] or bullets[:3])},
                ],
            }
        if intent == "process_flow":
            steps = []
            for item in slide.get("steps") or []:
                if isinstance(item, dict):
                    steps.append({"name": text(item.get("name") or item.get("label") or item.get("title") or item.get("step")) or title, "detail": text(item.get("detail") or item.get("desc") or item.get("description") or item.get("content")) or None})
                else:
                    item_text = text(item)
                    if item_text:
                        steps.append({"name": item_text, "detail": None})
            return {
                **base,
                "steps": steps or [{"name": item, "detail": None} for item in bullets[:4]],
            }
        if intent == "comparison":
            def side(value: Any, default_title: str, fallback: list[str]) -> dict:
                if isinstance(value, dict):
                    return {"title": text(value.get("title") or value.get("name")) or default_title, "bullets": first_list(value.get("bullets"), value.get("items"), value.get("points")) or fallback}
                items = text_list(value)
                return {"title": default_title, "bullets": items or fallback}

            return {
                **base,
                "left": side(slide.get("left"), "Option A", bullets[:3]),
                "right": side(slide.get("right"), "Option B", bullets[3:6] or bullets[:3]),
            }
        if intent == "timeline":
            events = []
            for item in slide.get("events") or []:
                if isinstance(item, dict):
                    events.append({"label": text(item.get("label") or item.get("title") or item.get("name") or item.get("event")) or title, "date": text(item.get("date") or item.get("time") or item.get("when")) or None, "detail": text(item.get("detail") or item.get("desc") or item.get("description") or item.get("content")) or None})
                else:
                    item_text = text(item)
                    if item_text:
                        events.append({"label": item_text})
            return {
                **base,
                "events": events or [{"label": item} for item in bullets[:4]],
            }
        if intent == "chart":
            chart = slide.get("chart") if isinstance(slide.get("chart"), dict) else {}
            labels = text_list(chart.get("labels") or chart.get("x") or chart.get("categories")) or bullets[:4]
            values = []
            for value in chart.get("values") or []:
                try:
                    values.append(float(value))
                except Exception:
                    pass
            if len(values) < len(labels):
                values = [float(i + 1) for i in range(len(labels))]
            return {
                **base,
                "chart": {
                    "chartType": chart.get("chartType") or chart.get("chart_type") or chart.get("type") or "bar",
                    "labels": labels[:6],
                    "series": chart.get("series") or [{"name": title, "values": values[:6]}],
                },
            }
        if intent == "swot":
            swot = slide.get("swot") if isinstance(slide.get("swot"), dict) else {}
            return {
                **base,
                "swot": {
                    "strengths": text_list(swot.get("strengths") or slide.get("strengths")),
                    "weaknesses": text_list(swot.get("weaknesses") or slide.get("weaknesses")),
                    "opportunities": text_list(swot.get("opportunities") or slide.get("opportunities")),
                    "threats": text_list(swot.get("threats") or slide.get("threats")),
                },
            }
        if intent == "roadmap":
            phases = []
            for item in slide.get("phases") or []:
                if isinstance(item, dict):
                    phases.append({"name": text(item.get("name") or item.get("phase") or item.get("title")) or title, "timeframe": text(item.get("timeframe") or item.get("time") or item.get("period")) or None, "deliverables": first_list(item.get("deliverables"), item.get("tasks"), item.get("items"), item.get("outputs"))})
                else:
                    item_text = text(item)
                    if item_text:
                        phases.append({"name": item_text, "deliverables": []})
            return {
                **base,
                "phases": phases or [{"name": item, "deliverables": []} for item in bullets[:3]],
            }
        if intent == "kpi":
            items = []
            for item in slide.get("items") or []:
                if isinstance(item, dict):
                    raw_value = item.get("value") if item.get("value") is not None else item.get("number")
                    items.append({"label": text(item.get("label") or item.get("name") or item.get("title")) or title, "value": text(raw_value), "unit": text(item.get("unit")) or None, "delta": text(item.get("delta") or item.get("change")) or None})
                else:
                    item_text = text(item)
                    if item_text:
                        items.append({"label": item_text, "value": ""})
            return {
                **base,
                "items": items or [{"label": item, "value": ""} for item in bullets[:3]],
            }
        if intent == "architecture":
            layers = []
            for item in slide.get("layers") or []:
                if isinstance(item, dict):
                    layers.append({"name": text(item.get("name") or item.get("layer") or item.get("title")) or title, "items": first_list(item.get("items"), item.get("components"), item.get("modules"), item.get("bullets"))})
                else:
                    item_text = text(item)
                    if item_text:
                        layers.append({"name": item_text, "items": []})
            return {
                **base,
                "layers": layers or [{"name": item, "items": []} for item in bullets[:3]],
            }
        if intent == "quote":
            return {**base, "quote": text(slide.get("quote") or slide.get("text")) or title, "author": text(slide.get("author")) or None}
        if intent == "divider":
            return {**base, "subtitle": text(slide.get("subtitle")) or title}
        if intent == "team":
            members = []
            for item in slide.get("members") or []:
                if isinstance(item, dict):
                    members.append({"name": text(item.get("name") or item.get("title") or item.get("label")) or title, "role": text(item.get("role") or item.get("position")) or None, "highlights": first_list(item.get("highlights"), item.get("bullets"), item.get("items"), item.get("points"))})
                else:
                    item_text = text(item)
                    if item_text:
                        members.append({"name": item_text, "highlights": []})
            return {
                **base,
                "members": members or [{"name": item, "highlights": []} for item in bullets[:3]],
            }

        return {
            **base,
            "intent": "text",
            "paragraphs": paragraphs or [f"{title} is an important part of {topic}."],
            "bullets": bullets[:5],
        }

    def _repair_slide_dict(self, s: dict, *, topic: str) -> dict:
        allowed_intents = {
            "cover", "agenda", "text", "timeline", "kpi", "comparison", "swot", "roadmap",
            "process_flow", "chart", "multi_column", "architecture", "quote", "divider", "team",
        }

        def as_str(v: Any) -> str:
            if v is None:
                return ""
            return v if isinstance(v, str) else str(v)

        def as_str_list(v: Any) -> list[str]:
            if v is None:
                return []
            if isinstance(v, str):
                t = v.strip()
                return [t] if t else []
            if isinstance(v, list):
                out: list[str] = []
                for item in v:
                    if item is None:
                        continue
                    if isinstance(item, str):
                        t = item.strip()
                        if t:
                            out.append(t)
                    elif isinstance(item, dict):
                        for key in ("label", "title", "name", "text", "content"):
                            value = item.get(key)
                            if isinstance(value, str) and value.strip():
                                out.append(value.strip())
                                break
                    else:
                        out.append(str(item))
                return out
            if isinstance(v, dict):
                for key in ("items", "bullets", "highlights", "paragraphs", "texts"):
                    if key in v:
                        return as_str_list(v.get(key))
                for key in ("label", "title", "name", "text", "content"):
                    value = v.get(key)
                    if isinstance(value, str) and value.strip():
                        return [value.strip()]
            return [str(v)]

        intent = as_str(
            s.get("intent")
            or s.get("type")
            or s.get("slideType")
            or s.get("slide_type")
            or s.get("pageType")
            or s.get("page_type")
            or s.get("layout")
        )
        if intent not in allowed_intents:
            for key in allowed_intents:
                if isinstance(s.get(key), dict):
                    intent = key
                    break
        if intent not in allowed_intents:
            intent = "text"
        wrapper = s.get(intent) if isinstance(s.get(intent), dict) else {}

        base = {
            "id": as_str(s.get("id") or wrapper.get("id") or new_id("slide")),
            "intent": intent,
            "section": as_str(s.get("section") or wrapper.get("section") or ""),
            "title": as_str(s.get("title") or wrapper.get("title") or topic),
            "notes": as_str_list(s.get("notes") if s.get("notes") is not None else wrapper.get("notes")),
        }

        if intent == "cover":
            return {**base, "subtitle": as_str(s.get("subtitle") or wrapper.get("subtitle")) or None, "tagline": as_str(s.get("tagline") or wrapper.get("tagline")) or None, "highlights": as_str_list(s.get("highlights") or wrapper.get("highlights"))}
        if intent == "agenda":
            return {**base, "items": as_str_list(s.get("items") if s.get("items") is not None else wrapper.get("items"))}
        if intent == "text":
            content = s.get("content") or wrapper.get("content")
            paragraphs = as_str_list(s.get("paragraphs") if s.get("paragraphs") is not None else wrapper.get("paragraphs"))
            bullets = as_str_list(s.get("bullets") if s.get("bullets") is not None else wrapper.get("bullets"))
            if not bullets:
                bullets = as_str_list(s.get("items") if s.get("items") is not None else wrapper.get("items"))
            if not paragraphs and not bullets and isinstance(content, str) and content.strip():
                paragraphs = [content.strip()]
            if isinstance(content, dict):
                paragraphs = paragraphs or as_str_list(content.get("paragraphs") or content.get("content") or content.get("text"))
                bullets = bullets or as_str_list(content.get("bullets") or content.get("items"))
            return {**base, "paragraphs": paragraphs, "bullets": bullets}
        if intent == "timeline":
            events = []
            for item in s.get("events") or wrapper.get("events") or []:
                if isinstance(item, str) and item.strip():
                    events.append({"label": item.strip()})
                elif isinstance(item, dict):
                    label = item.get("label") or item.get("title") or item.get("name") or item.get("event")
                    if isinstance(label, str) and label.strip():
                        event = {"label": label.strip()}
                        for src, dst in (("date", "date"), ("time", "date"), ("when", "date"), ("detail", "detail"), ("desc", "detail"), ("description", "detail"), ("content", "detail")):
                            value = item.get(src)
                            if isinstance(value, str) and value.strip():
                                event[dst] = value.strip()
                        events.append(event)
            return {**base, "events": events}
        if intent == "kpi":
            items = []
            for item in s.get("items") or wrapper.get("items") or []:
                if isinstance(item, str) and item.strip():
                    if ":" in item:
                        label, value = item.split(":", 1)
                        items.append({"label": label.strip(), "value": value.strip()})
                    else:
                        items.append({"label": item.strip(), "value": ""})
                elif isinstance(item, dict):
                    value = item.get("value")
                    if value is None:
                        value = item.get("val")
                    if value is None:
                        value = item.get("number")
                    out = {
                        "label": as_str(item.get("label") or item.get("name") or item.get("title") or "Metric"),
                        "value": as_str(value),
                    }
                    unit = as_str(item.get("unit"))
                    delta = as_str(item.get("delta") if item.get("delta") is not None else item.get("change"))
                    if unit:
                        out["unit"] = unit
                    if delta:
                        out["delta"] = delta
                    items.append(out)
            return {**base, "items": items}
        if intent == "comparison":
            def side(value: Any, default_title: str) -> dict:
                if isinstance(value, list):
                    return {"title": default_title, "bullets": as_str_list(value)}
                if isinstance(value, dict):
                    return {"title": as_str(value.get("title") or value.get("name") or default_title), "bullets": as_str_list(value.get("bullets") or value.get("items"))}
                return {"title": default_title, "bullets": []}
            return {**base, "left": side(s.get("left") or wrapper.get("left"), "Option A"), "right": side(s.get("right") or wrapper.get("right"), "Option B")}
        if intent == "swot":
            swot = s.get("swot") or wrapper.get("swot") or {}
            return {**base, "swot": {"strengths": as_str_list(swot.get("strengths") or swot.get("s") or s.get("strengths")), "weaknesses": as_str_list(swot.get("weaknesses") or swot.get("w") or s.get("weaknesses")), "opportunities": as_str_list(swot.get("opportunities") or swot.get("o") or s.get("opportunities")), "threats": as_str_list(swot.get("threats") or swot.get("t") or s.get("threats"))}}
        if intent == "roadmap":
            phases = []
            for item in s.get("phases") or wrapper.get("phases") or []:
                if isinstance(item, str) and item.strip():
                    phases.append({"name": item.strip(), "deliverables": []})
                elif isinstance(item, dict):
                    phases.append({"name": as_str(item.get("name") or item.get("phase") or item.get("title") or item.get("label") or "Phase"), "timeframe": as_str(item.get("timeframe") or item.get("time") or item.get("when") or item.get("period")) or None, "deliverables": as_str_list(item.get("deliverables") or item.get("tasks") or item.get("items") or item.get("outputs"))})
            return {**base, "phases": phases}
        if intent == "process_flow":
            steps = []
            for item in s.get("steps") or wrapper.get("steps") or []:
                if isinstance(item, str) and item.strip():
                    if ":" in item:
                        name, detail = item.split(":", 1)
                        steps.append({"name": name.strip(), "detail": detail.strip()})
                    else:
                        steps.append({"name": item.strip(), "detail": None})
                elif isinstance(item, dict):
                    steps.append({"name": as_str(item.get("name") or item.get("label") or item.get("title") or item.get("step") or "Step"), "detail": as_str(item.get("detail") or item.get("desc") or item.get("description") or item.get("content")) or None})
            return {**base, "steps": steps}
        if intent == "chart":
            chart = s.get("chart") or wrapper.get("chart") or {}
            chart_type = chart.get("chartType") or chart.get("chart_type") or chart.get("type") or "bar"
            if chart_type not in {"bar", "line", "pie"}:
                chart_type = "bar"
            series = []
            for item in chart.get("series") or chart.get("data") or []:
                if isinstance(item, dict):
                    values = []
                    for value in item.get("values") or item.get("data") or []:
                        try:
                            values.append(float(value))
                        except Exception:
                            pass
                    series.append({"name": as_str(item.get("name") or item.get("label") or item.get("title") or "Series"), "values": values})
            return {**base, "chart": {"chartType": chart_type, "labels": as_str_list(chart.get("labels") or chart.get("x") or chart.get("categories")), "series": series}}
        if intent == "multi_column":
            columns = []
            for item in s.get("columns") or wrapper.get("columns") or []:
                if isinstance(item, str) and item.strip():
                    columns.append({"title": item.strip(), "bullets": []})
                elif isinstance(item, dict):
                    columns.append({"title": as_str(item.get("title") or item.get("name") or item.get("label") or "Column"), "bullets": as_str_list(item.get("bullets") or item.get("items") or item.get("points") or item.get("highlights"))})
            return {**base, "columns": columns}
        if intent == "architecture":
            layers = []
            for item in s.get("layers") or wrapper.get("layers") or []:
                if isinstance(item, str) and item.strip():
                    layers.append({"name": item.strip(), "items": []})
                elif isinstance(item, dict):
                    layers.append({"name": as_str(item.get("name") or item.get("layer") or item.get("title") or item.get("label") or "Layer"), "items": as_str_list(item.get("items") or item.get("bullets") or item.get("components") or item.get("modules"))})
            return {**base, "layers": layers}
        if intent == "quote":
            return {**base, "quote": as_str(s.get("quote") or wrapper.get("quote") or s.get("text") or base["title"]), "author": as_str(s.get("author") if s.get("author") is not None else wrapper.get("author")) or None}
        if intent == "divider":
            return {**base, "subtitle": as_str(s.get("subtitle") if s.get("subtitle") is not None else wrapper.get("subtitle")) or None}
        if intent == "team":
            members = []
            for item in s.get("members") or wrapper.get("members") or []:
                if isinstance(item, str) and item.strip():
                    members.append({"name": item.strip(), "highlights": []})
                elif isinstance(item, dict):
                    members.append({"name": as_str(item.get("name") or item.get("title") or item.get("label") or "Member"), "role": as_str(item.get("role") or item.get("position")) or None, "highlights": as_str_list(item.get("highlights") or item.get("bullets") or item.get("items") or item.get("points"))})
            return {**base, "members": members}
        return {**base, "intent": "text", "paragraphs": [], "bullets": [base["title"]]}
