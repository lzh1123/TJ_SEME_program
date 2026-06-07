from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..ai.client import make_llm, parse_model
from .schemas import LLMJudgeScores

logger = logging.getLogger(__name__)

EVALUATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是资深 PPT 质量评估专家。你只输出 JSON，不要输出任何解释文字。\n\n"
            "任务：基于以下 PPT 大纲内容，按 5 个维度打分（每个维度 1-10 分，整数）：\n"
            "- structure_rationality: 章节划分是否逻辑清晰？过渡是否自然？\n"
            "- fact_accuracy: 内容中的事实表述是否与参考资料（如有）一致？是否存在编造？\n"
            "- logical_coherence: 各 slide 之间是否有清晰的叙事线索？\n"
            "- content_depth: 是否包含具体数据、案例、分析，而不仅仅是概述？\n"
            "- overall_quality: 整体作为沟通工具的质量如何？\n\n"
            "此外，给出 3-5 条具体的改进建议（suggestions 数组）。\n\n"
            "输出格式：\n"
            '{{\n'
            '  "structure_rationality": <int 1-10>,\n'
            '  "fact_accuracy": <int 1-10>,\n'
            '  "logical_coherence": <int 1-10>,\n'
            '  "content_depth": <int 1-10>,\n'
            '  "overall_quality": <int 1-10>,\n'
            '  "suggestions": ["建议1", "建议2", ...]\n'
            '}}',
        ),
        (
            "human",
            "## PPT 主题\n{topic}\n\n"
            "## PPT 大纲内容\n{outline_text}\n\n"
            "## 参考资料（如有）\n{reference_text}\n\n"
            "请基于以上信息，对 PPT 大纲进行质量评估。",
        ),
    ]
)


class LLMJudgeScoresWithSuggestions(BaseModel):
    structure_rationality: Optional[int] = None
    fact_accuracy: Optional[int] = None
    logical_coherence: Optional[int] = None
    content_depth: Optional[int] = None
    overall_quality: Optional[int] = None
    suggestions: List[str] = Field(default_factory=list)


class LLMJudge:
    """Uses an LLM to evaluate PPT outline quality on semantic dimensions."""

    def __init__(self):
        self._llm = None
        try:
            self._llm = make_llm()
        except Exception as e:
            logger.warning("LLMJudge: LLM not available: %s", e)

    @property
    def available(self) -> bool:
        return self._llm is not None

    def evaluate(
        self,
        topic: str,
        outline_text: str,
        reference_text: str = "",
    ) -> Dict[str, Any]:
        """Run LLM-as-Judge evaluation. Returns scores dict + suggestions list."""
        if not self._llm:
            return {
                "scores": LLMJudgeScores(),
                "suggestions": [],
            }

        try:
            raw = self._llm.invoke(
                EVALUATION_PROMPT.format_messages(
                    topic=topic,
                    outline_text=outline_text[:8000],
                    reference_text=reference_text[:4000] if reference_text else "无参考资料",
                )
            )
            content = getattr(raw, "content", str(raw))
            data = parse_model(LLMJudgeScoresWithSuggestions, content)

            return {
                "scores": LLMJudgeScores(
                    structure_rationality=data.structure_rationality,
                    fact_accuracy=data.fact_accuracy,
                    logical_coherence=data.logical_coherence,
                    content_depth=data.content_depth,
                    overall_quality=data.overall_quality,
                ),
                "suggestions": data.suggestions or [],
            }
        except Exception as e:
            logger.warning("LLMJudge evaluation failed: %s", e)
            return {
                "scores": LLMJudgeScores(),
                "suggestions": [],
            }
