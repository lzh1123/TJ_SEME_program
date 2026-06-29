from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate


JSON_ONLY = "你只输出严格 JSON，不要输出 Markdown 代码块、解释、前后缀文本。"


def intent_analysis_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        (
            "system",
            f"{JSON_ONLY}\n"
            "你是资深 PPT 信息架构师。请分析用户主题，输出 topic/audience/goal/tone/"
            "slideCount/preferredTheme。slideCount 至少 10 页，内容复杂时 15-20 页。",
        ),
        ("human", "{topic}"),
    ])


def presentation_plan_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        (
            "system",
            f"{JSON_ONLY}\n"
            "你是资深 PPT 结构规划师。基于输入分析规划 slides 列表。"
            "每个 slide 必须包含 id/intent/section/title/purpose。"
            "intent 只能使用 cover/agenda/text/timeline/kpi/comparison/swot/roadmap/"
            "process_flow/chart/multi_column/architecture/quote/divider/team。"
            "请保证结构完整：封面、议程、概念/背景、核心分析、案例/数据、方法/流程、总结。",
        ),
        ("human", "{analysis_json}"),
    ])


def dsl_generation_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        (
            "system",
            f"{JSON_ONLY}\n"
            "你是 PPT DSL Generator。输出必须匹配 PresentationDSL：title/audience/tone/theme/slides。\n"
            "所有 slide 必须包含 id、intent、section、title、notes(list[str])。\n"
            "严禁输出布局字段：x/y/w/h/fontSize/templateId/坐标/尺寸。\n"
            "字段规则：cover 使用 subtitle/tagline/highlights；agenda 使用 items；"
            "text 必须同时使用 paragraphs(list[str]) 与 bullets(list[str])；timeline 使用 events；"
            "kpi 使用 items；comparison 使用 left/right；swot 使用 swot；roadmap 使用 phases；"
            "process_flow 使用 steps；chart 使用 chart；multi_column 使用 columns；architecture 使用 layers。\n"
            "内容质量规则：\n"
            "1. 核心文本页不能只有要点。每个 text slide 必须有 1-2 个 paragraphs，每段 2-3 句，"
            "再配 3-5 条 bullets。\n"
            "2. paragraphs 负责解释、推理、背景和结论；bullets 负责提炼结构化要点，二者不能重复。\n"
            "3. 避免空泛词，优先给出具体问题、原因、方法、指标、案例或落地动作。\n"
            "4. 如果提供参考资料，必须吸收其中事实、数据、案例，避免只生成泛泛概念。\n"
            "5. 生成的页面类型应多样，不要连续大量使用纯 bullets 文本页。",
        ),
        ("human", "topic: {topic}\nanalysis: {analysis_json}\nplan: {plan_json}\ntheme: {theme_name}\n{rag_block}"),
    ])
