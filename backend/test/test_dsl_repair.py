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


def test_kimi_provider_uses_required_temperature():
    assert LLM_PROVIDERS["kimi"].temperature == 1.0
    assert LLM_PROVIDERS["qwen"].temperature == 0.0
