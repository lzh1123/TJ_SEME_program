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