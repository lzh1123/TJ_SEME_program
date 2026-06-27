from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ...domain.ids import new_id
from .llm_judge import LLMJudge
from .metrics import compute_rule_metrics, _extract_all_text
from .rag_eval import compute_rag_precision, compute_rag_recall, mark_chunks_used
from .schemas import (
    BleuScores,
    EvalResult,
    LLMJudgeScores,
    RougeLScores,
    RuleMetrics,
)

logger = logging.getLogger(__name__)


class Evaluator:
    """Orchestrates rule-based + LLM evaluation of PPT outlines."""

    def __init__(self):
        self._llm_judge = LLMJudge()

    def evaluate_single(
        self,
        presentation_id: str,
        topic: str,
        slides: List[Dict[str, Any]],
        reference_text: Optional[str] = None,
        enable_llm_judge: bool = True,
        requested_metrics: Optional[List[str]] = None,
    ) -> EvalResult:
        """Evaluate a single presentation. Returns EvalResult."""
        eval_id = new_id("eval")

        # Mark RAG chunks as used based on slide content
        slide_content = _extract_all_text(slides)
        try:
            mark_chunks_used(presentation_id, slide_content)
        except Exception as e:
            logger.debug("RAG chunk marking skipped: %s", e)

        # Compute rule-based metrics
        metrics_data, extracted_text = compute_rule_metrics(
            slides, reference_text, requested_metrics
        )

        # Build RuleMetrics
        rule_metrics = RuleMetrics()

        if "structure_completeness" in metrics_data:
            rule_metrics.structure_completeness = metrics_data["structure_completeness"]

        if "information_density" in metrics_data:
            rule_metrics.information_density = metrics_data["information_density"]

        if "content_diversity" in metrics_data:
            rule_metrics.content_diversity = metrics_data["content_diversity"]

        if "bleu" in metrics_data and metrics_data["bleu"] is not None:
            rule_metrics.bleu = metrics_data["bleu"]
        elif "bleu" in (requested_metrics or []) and reference_text:
            rule_metrics.bleu = BleuScores()

        if "rouge_l" in metrics_data and metrics_data["rouge_l"] is not None:
            rule_metrics.rouge_l = metrics_data["rouge_l"]
        elif "rouge" in (requested_metrics or []) and reference_text:
            rule_metrics.rouge_l = RougeLScores()

        if "rag_recall" in (requested_metrics or []):
            rule_metrics.rag_recall = compute_rag_recall(presentation_id)
            rule_metrics.rag_precision = compute_rag_precision(presentation_id)

        # LLM Judge
        llm_scores = None
        suggestions: List[str] = []
        if enable_llm_judge and self._llm_judge.available:
            result = self._llm_judge.evaluate(
                topic=topic,
                outline_text=extracted_text,
                reference_text=reference_text or "",
            )
            llm_scores = result.get("scores")
            suggestions = result.get("suggestions", [])

        # Compute overall score (weighted average)
        overall = self._compute_overall(rule_metrics, llm_scores)

        return EvalResult(
            eval_id=eval_id,
            presentation_id=presentation_id,
            topic=topic,
            rule_metrics=rule_metrics,
            llm_judge_metrics=llm_scores,
            suggestions=suggestions,
            overall_score=round(overall, 1),
        )

    def _compute_overall(
        self, rule: RuleMetrics, llm: Optional[LLMJudgeScores]
    ) -> float:
        """Compute weighted overall score 0-10."""
        parts: List[float] = []

        # Rule metrics → 0-10 scale
        parts.append(rule.structure_completeness * 10 * 0.15)
        parts.append(rule.information_density.score * 10 * 0.1)
        parts.append(rule.content_diversity.ttr * 10 * 0.05)

        if rule.rag_recall is not None:
            parts.append(rule.rag_recall * 10 * 0.1)

        # LLM metrics → 0-10 scale (weight: 60% total if available, else 0)
        if llm is not None:
            llm_values = [
                llm.structure_rationality,
                llm.fact_accuracy,
                llm.logical_coherence,
                llm.content_depth,
                llm.overall_quality,
            ]
            valid = [v for v in llm_values if v is not None]
            if valid:
                llm_avg = sum(valid) / len(valid)
                parts.append(llm_avg * 0.6)
            else:
                # No valid LLM scores — reweight rule metrics
                total_rule_weight = sum(
                    w for w in [0.15, 0.1, 0.05, 0.1] if w > 0
                )
                if total_rule_weight > 0:
                    factor = 1.0 / total_rule_weight
                    parts = [p * factor for p in parts]
        else:
            # No LLM scores — reweight rule metrics
            total_rule_weight = sum(w for w in [0.15, 0.1, 0.05, 0.1])
            if total_rule_weight > 0:
                factor = 1.0 / total_rule_weight
                parts = [p * factor for p in parts]

        return sum(parts)
