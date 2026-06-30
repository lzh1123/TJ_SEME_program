from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate


JSON_ONLY = "只输出严格 JSON。不要输出 Markdown 代码块、解释、前后缀文本。"

INTENTS = (
    "cover, agenda, text, timeline, kpi, comparison, swot, roadmap, "
    "process_flow, chart, multi_column, architecture, quote, divider, team"
)


def intent_analysis_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        (
            "system",
            f"{JSON_ONLY}\n"
            "你是资深 PPT 信息架构师。请使用中文分析用户主题，并只输出这些字段："
            "topic, audience, goal, tone, slideCount, preferredTheme。\n"
            "语言规则：如果用户使用中文，所有可读文本必须输出中文；不要把中文主题翻译成英文。\n"
            "页数规则：slideCount 必须接近 targetSlideCount，允许上下浮动 1 页。\n"
            "大纲不承载 PPT 视觉风格、颜色、模板或排版主题。preferredTheme 通常输出 null；"
            "除非用户明确给出 internal id，否则不要填主题描述。",
        ),
        ("human", "topic: {topic}\ntargetSlideCount: {target_slide_count}\npageCountPreset: {page_count_preset}"),
    ])


def presentation_plan_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        (
            "system",
            f"{JSON_ONLY}\n"
            "你是资深 PPT 结构规划师。请基于输入分析规划 slides 数组。\n"
            f"intent 只能使用：{INTENTS}。\n"
            "每个 slide 必须包含 id、intent、section、title、purpose。\n"
            "语言规则：所有 title、section、purpose 必须使用中文。\n"
            "页数规则：slides 数量必须接近 slideCount，允许上下浮动 1 页。\n"
            "结构规则：短主题也要主动补全合理教学结构，覆盖封面、目录、概念定义、背景/发展、核心方法、"
            "案例/数据、对比/流程/架构等至少一种结构化页面、总结。\n"
            "质量规则：不要产出只有标题的空页；不要让 Agenda 变成 Comparison；不要输出视觉风格字段。",
        ),
        ("human", "{analysis_json}"),
    ])


def dsl_generation_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        (
            "system",
            f"{JSON_ONLY}\n"
            "你是 PPT 大纲 DSL 生成专家。输出 PresentationDSL 兼容 JSON：title, audience, tone, slides。"
            "字段类型规则：title/audience/tone/theme 必须是字符串；所有列表元素必须是字符串；"
            "kpi.items[].value 必须是字符串，即使内容是数字也要加引号。"
            "不要在大纲中输出视觉风格、颜色、模板、坐标、尺寸、字体大小或排版参数。"
            "如果下游 schema 需要 theme，最多使用 paper_light 作为内部默认值，不把它当作大纲内容。\n"
            "语言规则：用户主题是中文时，所有可读内容必须是中文；禁止把“软件工程介绍”生成成英文大纲。\n"
            "页数规则：slides 数量必须接近 targetSlideCount，允许上下浮动 1 页。\n"
            "通用规则：每页必须有 id、intent、section、title、notes(list[str])；notes 至少 1 条，说明本页讲述目的。\n"
            "各页面类型质量约束：\n"
            "- cover: subtitle/tagline 至少一个；highlights 3 条，说明主题范围、受众价值、学习/汇报目标。\n"
            "- agenda: items 5-8 条，必须与后续主要章节对应，不能写成左右对比。\n"
            "- text: paragraphs 1-2 段，每段 2-3 句；bullets 3-5 条。段落负责解释和推理，bullets 负责结构化要点，二者不要重复。\n"
            "- chart: chart.chartType 为 bar/line/pie；labels 至少 4 个；series 至少 1 组，values 必须是数字；notes 说明图表要表达的洞察。\n"
            "- quote: quote 必须是与主题相关的观点句，author 可为“行业共识/课程总结/项目经验”等，不要空泛。\n"
            "- kpi: items 3-5 个，每个有 label/value/unit 或 delta，指标必须服务主题分析。\n"
            "- timeline: events 4-6 个，每个有 label，尽量有 date/time 和 detail，体现阶段演进。\n"
            "- comparison: left/right 都必须有 title；左右 bullets 各 3-5 条，必须比较真实对象，不能只写“左/右”。\n"
            "- swot: strengths/weaknesses/opportunities/threats 四象限各 2-4 条。\n"
            "- roadmap: phases 3-5 个，每个有 name/timeframe/deliverables，deliverables 2-4 条。\n"
            "- process_flow: steps 4-7 个，每个有 name/detail，体现先后关系和产出。\n"
            "- multi_column: columns 2-4 列，每列 title 明确，bullets 3-5 条。\n"
            "- architecture: layers 3-5 层，每层 name 明确，items 2-5 条，体现组成关系。\n"
            "- divider: subtitle 必须说明进入的新章节和承上启下关系。\n"
            "- team: members 3-6 个，每个有 name/role/highlights，适用于组织、角色、分工类主题；不适合时少用。\n"
            "内容深度规则：优先给出定义、原因、方法、适用场景、风险、评价指标、案例或落地动作；避免空话套话。\n"
            "如果提供参考资料，必须吸收其中事实、数据和案例。",
        ),
        (
            "human",
            "topic: {topic}\n"
            "targetSlideCount: {target_slide_count}\n"
            "analysis: {analysis_json}\n"
            "plan: {plan_json}\n"
            "internal_theme: {theme_name}\n"
            "{rag_block}",
        ),
    ])
