import os
from pathlib import Path
from typing import Callable, Optional

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

try:
    from .outline_prompt import outline_prompt_build
    from .outline_schema import OutlineBuildSchema, OutlinePromptSchema, PptPlanSchema
    from .parser import OutlineBuildParser, PptPlanParser
except ImportError:
    from outline_prompt import outline_prompt_build
    from outline_schema import OutlineBuildSchema, OutlinePromptSchema, PptPlanSchema
    from parser import OutlineBuildParser, PptPlanParser


load_dotenv()

# 大模型创建工厂
def _make_llm():
    model = os.getenv("LLM_MODEL", "DeepSeek-R1")
    api_base = os.getenv("LLM_API_BASE", "https://llmapi.tongji.edu.cn/v1")
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")
    timeout = float(os.getenv("LLM_TIMEOUT", "60"))

    return ChatOpenAI(
        model=model,
        openai_api_base=api_base,
        openai_api_key=api_key,
        temperature=0,
        timeout=timeout,
        max_retries=2,
    )


def _invoke_llm_text(llm: ChatOpenAI, messages, stream: bool, on_token: Optional[Callable[[str], None]] = None) -> str:
    if not stream:
        resp = llm.invoke(messages)
        return getattr(resp, "content", "") or ""

    parts = []
    for chunk in llm.stream(messages):
        delta = getattr(chunk, "content", None)
        if not delta:
            continue
        parts.append(delta)
        if on_token:
            on_token(delta)
    return "".join(parts)


# 大纲生成
def outline_build(outline_prompt: OutlinePromptSchema, stream: bool = False) -> OutlineBuildSchema:
    prompt_path = Path(__file__).resolve().parents[1] / "prompt" / "outline_build.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")

    parser = OutlineBuildParser()
    llm = _make_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{outline_prompt_json}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    outline_prompt_json = outline_prompt.model_dump_json(
        ensure_ascii=False,
        indent=2,
    )

    messages = prompt.format_messages(outline_prompt_json=outline_prompt_json)
    if stream:
        print("=== DeepSeek 输出流：结构化大纲 ===", flush=True)
    raw_text = _invoke_llm_text(
        llm,
        messages,
        stream=stream,
        on_token=(lambda t: print(t, end="", flush=True)) if stream else None,
    )
    if stream:
        print("\n=== DeepSeek 输出流结束：结构化大纲 ===", flush=True)
    return parser.parse(raw_text)

# 错误回调大纲
def _fallback_outline(topic: str) -> OutlineBuildSchema:
    return OutlineBuildSchema(
        title=topic,
        slides=[
            {
                "slide_number": 1,
                "section_title": "概览",
                "slide_title": "软件工程是什么",
                "key_points": [
                    "以工程化方法开发与维护软件系统",
                    "关注质量、成本、进度与风险控制",
                    "强调过程、规范、工具与协作",
                ],
                "suggested_visuals": ["软件生命周期示意图"],
                "speaker_notes": [],
            },
            {
                "slide_number": 2,
                "section_title": "价值",
                "slide_title": "为什么需要软件工程",
                "key_points": [
                    "规模与复杂度提升带来失控风险",
                    "需求变化需要可控迭代与反馈闭环",
                    "降低缺陷与返工成本，提升可维护性",
                ],
                "suggested_visuals": ["缺陷修复成本曲线图"],
                "speaker_notes": [],
            },
            {
                "slide_number": 3,
                "section_title": "过程",
                "slide_title": "典型开发过程模型",
                "key_points": [
                    "瀑布：阶段顺序、文档驱动",
                    "迭代/增量：分阶段交付可用版本",
                    "敏捷：短迭代、持续反馈、拥抱变化",
                ],
                "suggested_visuals": ["瀑布 vs 迭代 vs Scrum 对比"],
                "speaker_notes": [],
            },
            {
                "slide_number": 4,
                "section_title": "核心活动",
                "slide_title": "需求与设计",
                "key_points": [
                    "需求：获取、分析、规格、验收标准",
                    "架构：分层/模块化，关注可扩展与可演进",
                    "设计原则：高内聚、低耦合、单一职责",
                ],
                "suggested_visuals": ["架构分层图"],
                "speaker_notes": [],
            },
            {
                "slide_number": 5,
                "section_title": "质量保障",
                "slide_title": "测试与质量保证",
                "key_points": [
                    "测试层级：单元、集成、系统、验收",
                    "自动化：CI 中运行测试与静态检查",
                    "度量：缺陷率、覆盖率、变更失败率等",
                ],
                "suggested_visuals": ["测试金字塔"],
                "speaker_notes": [],
            },
            {
                "slide_number": 6,
                "section_title": "工程实践",
                "slide_title": "DevOps 与持续交付",
                "key_points": [
                    "CI/CD：持续集成、持续交付/部署",
                    "可观测性：监控、告警、日志与追踪",
                    "发布策略：灰度、回滚、变更控制",
                ],
                "suggested_visuals": ["CI/CD 流水线示意图"],
                "speaker_notes": [],
            },
            {
                "slide_number": 7,
                "section_title": "总结",
                "slide_title": "总结与建议",
                "key_points": [
                    "以需求为起点，以质量为底线",
                    "小步快跑、持续反馈、持续改进",
                    "选择适合团队与项目的过程与工具",
                ],
                "suggested_visuals": ["路线图/要点清单"],
                "speaker_notes": [],
            },
        ],
    )


def _load_template_catalog() -> dict:
    import json

    templates_path = Path(__file__).resolve().parents[1] / "ppt_service" / "Office-PowerPoint-MCP-Server" / "slide_layout_templates.json"
    data = json.loads(templates_path.read_text(encoding="utf-8"))
    templates = data.get("templates", {}) or {}
    color_schemes = list((data.get("color_schemes", {}) or {}).keys())

    templates_brief = []
    for template_id, tpl in templates.items():
        roles = []
        for el in tpl.get("elements", []) or []:
            role = el.get("role")
            el_type = el.get("type")
            if role and el_type:
                roles.append(f"{role}:{el_type}")
        templates_brief.append(
            {
                "template_id": template_id,
                "name": tpl.get("name", ""),
                "description": tpl.get("description", ""),
                "layout_type": tpl.get("layout_type", ""),
                "roles": roles,
            }
        )

    return {
        "templates": templates_brief,
        "color_schemes": color_schemes,
    }


def _fallback_ppt_plan(outline: OutlineBuildSchema) -> PptPlanSchema:
    section_titles = []
    for s in outline.slides:
        if s.section_title and (not section_titles or section_titles[-1] != s.section_title):
            section_titles.append(s.section_title)

    agenda = "\n\n".join(f"{i+1}. {t}" for i, t in enumerate(section_titles)) if section_titles else "\n\n".join(
        f"{i+1}. {s.slide_title}" for i, s in enumerate(outline.slides[:6])
    )

    template_sequence = [
        {
            "template_id": "title_slide",
            "content": {
                "title": outline.title,
                "subtitle": "结构化大纲驱动的自动化生成",
                "author": "AI Generator",
            },
        },
        {
            "template_id": "agenda_slide",
            "content": {
                "title": "目录",
                "agenda_items": agenda,
            },
        },
    ]

    for s in outline.slides:
        template_id = "text_with_image"
        hint = " ".join((s.suggested_visuals or []) + [s.slide_title]).lower()
        if "对比" in hint or "vs" in hint or "比较" in hint:
            template_id = "two_column_text"
        elif "流程" in hint or "生命周期" in hint or "pipeline" in hint:
            template_id = "process_flow"
        elif "数据" in hint or "表" in hint or "指标" in hint:
            template_id = "key_metrics_dashboard"

        if template_id == "two_column_text":
            left = "\n".join(f"• {p}" for p in (s.key_points[:3] or []))
            right = "\n".join(f"• {p}" for p in (s.key_points[3:6] or []))
            template_sequence.append(
                {
                    "template_id": template_id,
                    "content": {
                        "title": s.slide_title,
                        "content_left": left or "• 要点 A\n• 要点 B\n• 要点 C",
                        "content_right": right or "• 要点 D\n• 要点 E\n• 要点 F",
                    },
                }
            )
        elif template_id == "process_flow":
            steps = [p.replace("：", " - ") for p in (s.key_points[:5] or [])]
            template_sequence.append(
                {
                    "template_id": template_id,
                    "content": {
                        "title": s.slide_title,
                        "steps": "\n".join(steps) if steps else "需求\n设计\n开发\n测试\n交付",
                    },
                }
            )
        elif template_id == "key_metrics_dashboard":
            template_sequence.append(
                {
                    "template_id": template_id,
                    "content": {
                        "title": s.slide_title,
                        "metric_1_value": "99.9%",
                        "metric_1_label": "可用性",
                        "metric_2_value": "2x",
                        "metric_2_label": "交付效率",
                        "metric_3_value": "↓30%",
                        "metric_3_label": "缺陷率",
                    },
                }
            )
        else:
            template_sequence.append(
                {
                    "template_id": template_id,
                    "content": {
                        "title": s.slide_title,
                        "content": "\n".join(f"• {p}" for p in (s.key_points[:6] or [])),
                    },
                }
            )

    template_sequence.append(
        {
            "template_id": "thank_you_slide",
            "content": {
                "title": "谢谢",
                "contact": "Q & A",
            },
        }
    )

    return PptPlanSchema(
        title=outline.title,
        color_scheme="modern_blue",
        template_sequence=template_sequence,
        charts=[],
        optimize_text=True,
        enhance_slides=True,
    )


def ppt_plan_build(outline: OutlineBuildSchema, stream: bool = False) -> PptPlanSchema:
    import os
    import json

    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        return _fallback_ppt_plan(outline)

    catalog = _load_template_catalog()
    parser = PptPlanParser()
    llm = _make_llm()

    system_prompt = (
        "你是一名资深演示文稿设计师与信息架构师。"
        "你将收到一份结构化 PPT 大纲（JSON），以及可用的模板库（JSON）。"
        "你的任务是生成一个 PPT 生成计划（JSON），必须严格遵循 format_instructions。"
        "\n"
        "要求：\n"
        "1) 使用 template_sequence 驱动 create_presentation_from_templates 生成高质量版式；\n"
        "2) 模板必须从提供的 templates 中选择；\n"
        "3) content 映射必须匹配模板 role（例如 title/subtitle/content/agenda_items/...），不要杜撰不存在的 role；\n"
        "4) 每页信息密度适中：正文最多 5-7 条要点，每条尽量短；\n"
        "5) 必须包含：title_slide + agenda_slide + thank_you_slide；\n"
        "6) color_scheme 从提供的 color_schemes 里选择，偏学术/教学风格；\n"
        "7) 如果大纲里出现“对比/曲线/趋势/指标”等，优先用 chart_comparison 或 key_metrics_dashboard；\n"
        "8) optimize_text=true, enhance_slides=true。\n"
        "9) 只输出 JSON，不要使用 Markdown 代码块，不要加入任何额外包装字段（例如 ppt_generation_plan、slides、slide_number）。\n"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input_json}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    input_json = {
        "outline": outline.model_dump(),
        "template_catalog": catalog,
    }

    try:
        input_json_str = json.dumps(input_json, ensure_ascii=False, indent=2)
        messages = prompt.format_messages(input_json=input_json_str)
        if stream:
            print("=== DeepSeek 输出流：PPT 生成计划 ===", flush=True)
        raw_text = _invoke_llm_text(
            llm,
            messages,
            stream=stream,
            on_token=(lambda t: print(t, end="", flush=True)) if stream else None,
        )
        if stream:
            print("\n=== DeepSeek 输出流结束：PPT 生成计划 ===", flush=True)
        return parser.parse(raw_text)
    except Exception:
        if stream:
            print("=== 注意：模型输出未能通过 Schema 解析，已回退到规则生成的 PPT 计划 ===", flush=True)
        return _fallback_ppt_plan(outline)

# 构建大纲完整工作流
def build_outline_bundle(topic: str, stream: bool = False) -> dict:
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        outline = _fallback_outline(topic)
        return {
            "outline_prompt": None,
            "outline": outline,
        }

    try:
        if stream:
            print("=== 阶段 1/3：生成大纲提示词 ===", flush=True)
        outline_prompt = outline_prompt_build(topic, stream=stream)
        if stream:
            print("=== 阶段 2/3：生成结构化大纲 ===", flush=True)
        outline = outline_build(outline_prompt, stream=stream)
    except Exception:
        outline = _fallback_outline(topic)
        return {
            "outline_prompt": None,
            "outline": outline,
        }
    return {
        "outline_prompt": outline_prompt,
        "outline": outline,
    }


def build_ppt_bundle(topic: str, stream: bool = False) -> dict:
    bundle = build_outline_bundle(topic, stream=stream)
    outline = bundle["outline"]
    if stream:
        print("=== 阶段 3/3：生成 PPT 生成计划 ===", flush=True)
    plan = ppt_plan_build(outline, stream=stream)
    return {
        **bundle,
        "ppt_plan": plan,
    }


if __name__ == "__main__":
    topic = input("输入主题： ").strip()
    bundle = build_outline_bundle(topic)
    print(bundle["outline"].model_dump_json(ensure_ascii=False, indent=2))
