from pydantic import BaseModel, Field
from typing import List


class InputAnalysis(BaseModel):
    input_type: str = Field(
        description="输入类型，short_topic 或 long_topic"
    )
    core_topic: str = Field(
        description="核心主题"
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="提取出的关键要点列表"
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="模型自动补充的合理假设"
    )


class OutlineRequirements(BaseModel):
    target_audience: str = Field(
        description="目标受众"
    )
    presentation_goal: str = Field(
        description="演讲目标"
    )
    tone: str = Field(
        description="整体语气风格，如正式、学术、商务、简洁等"
    )
    slide_count: str = Field(
        description="建议页数，如 8-10 页"
    )
    structure: List[str] = Field(
        default_factory=list,
        description="PPT整体结构章节列表"
    )


class OutlinePromptSchema(BaseModel):
    input_analysis: InputAnalysis = Field(
        description="输入内容分析结果"
    )

    expanded_topic: str = Field(
        description="扩展后的完整主题描述"
    )

    ppt_prompt: str = Field(
        description="用于后续生成 PPT 内容的高质量 Prompt"
    )

    outline_requirements: OutlineRequirements = Field(
        description="PPT大纲生成要求"
    )


class OutlineSlide(BaseModel):
    slide_number: int = Field(
        description="幻灯片序号，从 1 开始"
    )
    section_title: str = Field(
        description="所属章节标题，用于分组展示"
    )
    slide_title: str = Field(
        description="该页标题"
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="该页需要呈现的要点列表（用于正文）"
    )
    suggested_visuals: List[str] = Field(
        default_factory=list,
        description="建议的图表/示意图/案例形式（可选）"
    )
    speaker_notes: List[str] = Field(
        default_factory=list,
        description="演讲者备注（可选）"
    )


class OutlineBuildSchema(BaseModel):
    title: str = Field(
        description="整套 PPT 的标题（通常与 expanded_topic 一致或更精炼）"
    )
    slides: List[OutlineSlide] = Field(
        default_factory=list,
        description="按顺序排列的幻灯片列表"
    )
