from __future__ import annotations

from ppt_backend.services.evaluation.metrics import compute_rule_metrics

from backend.test.sample_deck_fixtures import sample_full_dsl


def test_rule_metrics_score_structured_generated_content():
    metrics, extracted = compute_rule_metrics(
        sample_full_dsl()["slides"],
        reference_text="Slideon validates backend API, RAG, and export quality.",
    )
    assert metrics["structure_completeness"] >= 0.9
    assert metrics["information_density"].score >= 0
    assert metrics["content_diversity"].total_terms > 0
    assert metrics["bleu"].bleu_1 >= 0
    assert metrics["rouge_l"].f1 >= 0
    assert "Backend API Capability" in extracted
