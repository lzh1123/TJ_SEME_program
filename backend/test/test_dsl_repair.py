from ppt_backend.domain.dsl import PresentationDSL
from ppt_backend.services.ai.model_config import LLM_PROVIDERS
from ppt_backend.services.ai.pipeline import AiPipeline
from ppt_backend.services.ai.schemas import IntentAnalysis


def test_repair_dsl_dict_coerces_qwen_like_types():
    pipeline = AiPipeline.__new__(AiPipeline)
    analysis = IntentAnalysis(
        topic="Battery technology report",
        audience="General audience",
        tone="Clear and professional",
        slideCount=3,
    )

    repaired = pipeline._repair_dsl_dict(
        {
            "title": "Battery technology report",
            "audience": ["investors", "engineers", "policy analysts"],
            "tone": "Analytical",
            "slides": [
                {
                    "id": "s1",
                    "intent": "kpi",
                    "section": "Metrics",
                    "title": "Core metrics",
                    "notes": ["Explain key metrics"],
                    "items": [{"label": "Market size", "value": 115, "unit": "B"}],
                }
            ],
        },
        topic="Battery technology report",
        analysis=analysis,
        theme_name="paper_light",
    )

    assert repaired["audience"] == "investors / engineers / policy analysts"
    assert repaired["slides"][0]["items"][0]["value"] == "115"
    PresentationDSL.model_validate(repaired)


def test_repair_dsl_dict_accepts_descriptive_invalid_intents_without_templates():
    pipeline = AiPipeline.__new__(AiPipeline)
    analysis = IntentAnalysis(
        topic="Battery technology report",
        audience="General audience",
        tone="Clear and professional",
        slideCount=2,
    )

    repaired = pipeline._repair_dsl_dict(
        {
            "title": "Battery technology report",
            "slides": [
                {
                    "id": 1,
                    "intent": "Build context and define decision value",
                    "section": "Opening",
                    "title": "Why battery routes matter",
                    "notes": ["Frame the analysis scope"],
                    "items": [
                        {"label": "Lithium reserve life", "value": "23", "unit": "years"},
                        {"label": "Recycling share", "value": "18", "unit": "%"},
                    ],
                },
                {
                    "id": 2,
                    "intent": "Show market structure and technology landscape",
                    "section": "Market",
                    "title": "Market landscape",
                    "notes": ["Explain external constraints"],
                    "paragraphs": ["Policy, supply chain, and cost jointly shape the route choice."],
                },
            ],
        },
        topic="Battery technology report",
        analysis=analysis,
        theme_name="paper_light",
    )

    validated = PresentationDSL.model_validate(repaired)
    assert [slide.intent for slide in validated.slides] == ["text", "text"]
    assert validated.slides[0].title == "Why battery routes matter"
    assert validated.slides[0].bullets[0] == "Lithium reserve life"


def test_glm_provider_uses_required_temperature():
    assert LLM_PROVIDERS["glm"].temperature == 1.0
    assert LLM_PROVIDERS["glm"].model == "glm-4.7"
    assert LLM_PROVIDERS["qwen"].temperature == 0.0


def test_normalize_generated_dsl_uses_chinese_fallback_copy():
    pipeline = AiPipeline.__new__(AiPipeline)
    dsl = PresentationDSL.model_validate(
        {
            "title": "Sleep quality report",
            "audience": "Students",
            "tone": "Academic",
            "slides": [
                {"id": "s1", "intent": "text", "section": "Intro", "title": "Sleep quality", "notes": []},
                {"id": "s2", "intent": "agenda", "section": "Intro", "title": "Agenda", "notes": []},
                {"id": "s3", "intent": "comparison", "section": "Compare", "title": "Sleep states", "notes": [], "left": {"title": "", "bullets": []}, "right": {"title": "", "bullets": []}},
            ],
        }
    )

    normalized = pipeline._normalize_generated_dsl(dsl)
    payload = normalized.model_dump_json(by_alias=True)

    forbidden = [
        "Explain the core concept",
        "Analyze key problems",
        "should be explained from background",
        "Core concepts",
        "Option A",
        "Option B",
    ]
    for text in forbidden:
        assert text not in payload


def test_normalize_generated_dsl_does_not_fabricate_structured_facts():
    pipeline = AiPipeline.__new__(AiPipeline)
    dsl = PresentationDSL.model_validate(
        {
            "title": "Sleep quality report",
            "audience": "Students",
            "tone": "Academic",
            "slides": [
                {"id": "s1", "intent": "kpi", "section": "Metrics", "title": "Missing metrics", "notes": [], "items": []},
                {"id": "s2", "intent": "timeline", "section": "History", "title": "Missing timeline", "notes": [], "events": []},
                {
                    "id": "s3",
                    "intent": "chart",
                    "section": "Data",
                    "title": "Partial chart",
                    "notes": [],
                    "chart": {"chartType": "bar", "labels": ["A", "B", "C"], "series": [{"name": "Observed", "values": [1]}]},
                },
                {"id": "s4", "intent": "roadmap", "section": "Plan", "title": "Missing roadmap", "notes": [], "phases": []},
                {"id": "s5", "intent": "process_flow", "section": "Steps", "title": "Missing steps", "notes": [], "steps": []},
            ],
        }
    )

    normalized = pipeline._normalize_generated_dsl(dsl)

    assert normalized.slides[0].items == []
    assert normalized.slides[1].events == []
    assert normalized.slides[2].chart.labels == ["A", "B", "C"]
    assert normalized.slides[2].chart.series[0].values == [1]
    assert normalized.slides[3].phases == []
    assert normalized.slides[4].steps == []
