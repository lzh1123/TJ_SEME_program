from ppt_backend.services.ai.pipeline import AiPipeline
from ppt_backend.services.ai.schemas import IntentAnalysis


def test_repair_dsl_dict_coerces_qwen_like_types():
    pipeline = AiPipeline.__new__(AiPipeline)
    analysis = IntentAnalysis(
        topic="游戏开发项目介绍",
        audience="通用受众",
        tone="清晰专业",
        slideCount=3,
    )

    repaired = pipeline._repair_dsl_dict(
        {
            "title": "游戏开发项目介绍",
            "audience": ["游戏爱好者", "青少年", "教育工作者"],
            "tone": "教学友好",
            "slides": [
                {
                    "id": "s1",
                    "intent": "kpi",
                    "section": "指标",
                    "title": "核心指标",
                    "notes": ["说明关键指标"],
                    "items": [{"label": "最高在线人数", "value": 115, "unit": "人"}],
                }
            ],
        },
        topic="游戏开发项目介绍",
        analysis=analysis,
        theme_name="paper_light",
    )

    assert repaired["audience"] == "游戏爱好者、青少年、教育工作者"


def test_repair_slide_dict_coerces_kpi_values_to_strings():
    pipeline = AiPipeline.__new__(AiPipeline)

    repaired = pipeline._repair_slide_dict(
        {
            "id": "s1",
            "intent": "kpi",
            "section": "指标",
            "title": "核心指标",
            "notes": ["说明关键指标"],
            "items": [{"label": "最高在线人数", "value": 115, "unit": "人"}],
        },
        topic="游戏开发项目介绍",
    )

    assert repaired["items"][0]["value"] == "115"
