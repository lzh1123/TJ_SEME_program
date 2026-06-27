from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvalRequest(BaseModel):
    model_config = {"extra": "forbid"}

    reference_text: Optional[str] = None
    enable_llm_judge: bool = True
    metrics: List[str] = Field(
        default_factory=lambda: [
            "structure", "density", "diversity", "bleu", "rouge",
            "rag_recall", "llm_judge",
        ]
    )


class DensityMetrics(BaseModel):
    avg_bullets_per_slide: float = 0.0
    avg_words_per_slide: float = 0.0
    avg_paragraphs_per_slide: float = 0.0
    score: float = 0.0


class DiversityMetrics(BaseModel):
    ttr: float = 0.0
    unique_terms: int = 0
    total_terms: int = 0


class BleuScores(BaseModel):
    bleu_1: float = 0.0
    bleu_2: float = 0.0
    bleu_3: float = 0.0
    bleu_4: float = 0.0


class RougeLScores(BaseModel):
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0


class RuleMetrics(BaseModel):
    structure_completeness: float = 0.0
    information_density: DensityMetrics = Field(default_factory=DensityMetrics)
    content_diversity: DiversityMetrics = Field(default_factory=DiversityMetrics)
    bleu: Optional[BleuScores] = None
    rouge_l: Optional[RougeLScores] = None
    rag_recall: Optional[float] = None
    rag_precision: Optional[float] = None


class LLMJudgeScores(BaseModel):
    structure_rationality: Optional[int] = None
    fact_accuracy: Optional[int] = None
    logical_coherence: Optional[int] = None
    content_depth: Optional[int] = None
    overall_quality: Optional[int] = None


class EvalResult(BaseModel):
    eval_id: str
    presentation_id: str
    topic: str = ""
    rule_metrics: RuleMetrics = Field(default_factory=RuleMetrics)
    llm_judge_metrics: Optional[LLMJudgeScores] = None
    suggestions: List[str] = Field(default_factory=list)
    overall_score: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EvalReport(BaseModel):
    eval_id: str
    results: List[EvalResult] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class BatchEvalConfig(BaseModel):
    name: str
    use_rag: bool = True
    theme: Optional[str] = None


class BatchEvalRequest(BaseModel):
    model_config = {"extra": "forbid"}

    configs: List[BatchEvalConfig]
    topics: List[str]
    metrics: List[str] = Field(
        default_factory=lambda: [
            "structure", "density", "bleu", "rag_recall", "llm_judge",
        ]
    )
    reference_texts: Dict[str, str] = Field(default_factory=dict)
