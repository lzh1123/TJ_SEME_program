from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from .schemas import BleuScores, DensityMetrics, DiversityMetrics, RougeLScores


def compute_structure_completeness(slides: List[Dict[str, Any]]) -> float:
    """Score 0-1 based on presence of key sections and intent variety."""
    if not slides:
        return 0.0

    intents = [s.get("intent", "") for s in slides]

    score = 0.0

    # Has cover (0.2)
    if "cover" in intents:
        score += 0.2

    # Has agenda/toc (0.15)
    if "agenda" in intents:
        score += 0.15

    # Has content pages (0.25) — at least 3 non-cover/non-divider content slides
    content_intents = [
        i for i in intents
        if i not in ("cover", "agenda", "divider")
    ]
    if len(content_intents) >= 3:
        score += 0.25
    elif len(content_intents) >= 1:
        score += 0.1

    # Has conclusion/closing (0.15)
    last_slides = intents[-2:] if len(intents) >= 2 else intents
    if any(i in ("divider", "quote", "text") for i in last_slides):
        score += 0.15

    # Intent variety (0.25) — variety of slide types used
    unique_intents = len(set(intents))
    if unique_intents >= 8:
        score += 0.25
    elif unique_intents >= 5:
        score += 0.15
    elif unique_intents >= 3:
        score += 0.1

    return min(score, 1.0)


def compute_information_density(slides: List[Dict[str, Any]]) -> DensityMetrics:
    """Compute density metrics from slide content."""
    if not slides:
        return DensityMetrics()

    total_bullets = 0
    total_words = 0
    total_paragraphs = 0
    content_slide_count = 0

    for s in slides:
        intent = s.get("intent", "")
        if intent in ("cover", "divider"):
            continue
        content_slide_count += 1

        bullets = s.get("bullets", []) or []
        if isinstance(bullets, list):
            total_bullets += len(bullets)

        paragraphs = s.get("paragraphs", []) or []
        if isinstance(paragraphs, list):
            total_paragraphs += len(paragraphs)

        # Count words across all text fields
        text_fields = [
            s.get("title", ""),
            s.get("subtitle", ""),
            s.get("quote", ""),
            *[str(b) for b in bullets],
            *[str(p) for p in paragraphs],
            *[str(n) for n in (s.get("notes", []) or [])],
        ]
        for field in text_fields:
            total_words += len(re.findall(r"[\w一-鿿]+", str(field)))

    if content_slide_count == 0:
        return DensityMetrics()

    avg_bullets = total_bullets / content_slide_count
    avg_words = total_words / content_slide_count
    avg_paragraphs = total_paragraphs / content_slide_count

    # Score: normalize to 0-1 (target: ~4-6 bullets, ~100-200 words per slide)
    bullet_score = min(avg_bullets / 5.0, 1.0)
    word_score = min(avg_words / 150.0, 1.0)
    overall_score = (bullet_score * 0.5 + word_score * 0.5)

    return DensityMetrics(
        avg_bullets_per_slide=round(avg_bullets, 2),
        avg_words_per_slide=round(avg_words, 1),
        avg_paragraphs_per_slide=round(avg_paragraphs, 2),
        score=round(overall_score, 3),
    )


def compute_content_diversity(slides: List[Dict[str, Any]]) -> DiversityMetrics:
    """Compute Type-Token Ratio (TTR) for content diversity."""
    all_terms: List[str] = []

    for s in slides:
        text_fields = [
            s.get("title", ""),
            s.get("subtitle", ""),
            s.get("quote", ""),
            *[str(b) for b in (s.get("bullets", []) or [])],
            *[str(p) for p in (s.get("paragraphs", []) or [])],
            *[str(n) for n in (s.get("notes", []) or [])],
        ]
        for field in text_fields:
            # Split Chinese text into characters, English into words
            tokens = re.findall(r"[\w一-鿿]+", str(field).lower())
            all_terms.extend(tokens)

    total = len(all_terms)
    unique = len(set(all_terms))

    if total == 0:
        return DiversityMetrics()

    ttr = round(unique / total, 3)
    return DiversityMetrics(ttr=ttr, unique_terms=unique, total_terms=total)


def _extract_all_text(slides: List[Dict[str, Any]]) -> str:
    """Extract all text content from slides into a single string."""
    parts = []
    for s in slides:
        for field in ["title", "subtitle", "quote"]:
            v = s.get(field)
            if isinstance(v, str) and v.strip():
                parts.append(v.strip())
        for list_field in ["bullets", "paragraphs", "notes"]:
            items = s.get(list_field, []) or []
            for item in items:
                if isinstance(item, str) and item.strip():
                    parts.append(item.strip())
    return " ".join(parts)


def _ngram_counts(tokens: List[str], n: int) -> Counter:
    """Count n-grams in token list."""
    return Counter(tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1))


def compute_bleu(reference: str, candidate: str, max_n: int = 4) -> BleuScores:
    """Compute BLEU-1 through BLEU-4 scores."""
    if not reference or not candidate:
        return BleuScores()

    # Use character-level for Chinese, word-level for mixed
    ref_chars = list(reference)
    cand_chars = list(candidate)

    scores: Dict[str, float] = {}
    for n in range(1, max_n + 1):
        if len(cand_chars) < n or len(ref_chars) < n:
            scores[f"bleu_{n}"] = 0.0
            continue

        ref_ngrams = _ngram_counts(ref_chars, n)
        cand_ngrams = _ngram_counts(cand_chars, n)

        match_count = sum(
            min(cand_ngrams[ng], ref_ngrams.get(ng, 0))
            for ng in cand_ngrams
        )
        total_count = max(len(cand_chars) - n + 1, 1)

        precision = match_count / total_count if total_count > 0 else 0.0

        # Brevity penalty
        ref_len = len(ref_chars)
        cand_len = len(cand_chars)
        bp = math.exp(1 - ref_len / cand_len) if cand_len < ref_len and cand_len > 0 else 1.0

        scores[f"bleu_{n}"] = round(precision * bp, 4)

    return BleuScores(**scores)


def compute_rouge_l(reference: str, candidate: str) -> RougeLScores:
    """Compute ROUGE-L (Longest Common Subsequence) scores."""
    if not reference or not candidate:
        return RougeLScores()

    ref_chars = list(reference)
    cand_chars = list(candidate)

    # LCS using dynamic programming (optimized for char-level)
    m, n = len(ref_chars), len(cand_chars)
    if m == 0 or n == 0:
        return RougeLScores()

    # Use 1D DP for memory efficiency
    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if ref_chars[i - 1] == cand_chars[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr

    lcs_len = prev[n]

    precision = lcs_len / n if n > 0 else 0.0
    recall = lcs_len / m if m > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return RougeLScores(
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
    )


def compute_rule_metrics(
    slides: List[Dict[str, Any]],
    reference_text: Optional[str] = None,
    requested_metrics: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], str]:
    """Compute all requested rule-based metrics. Returns (metrics_dict, extracted_text)."""
    if requested_metrics is None:
        requested_metrics = ["structure", "density", "diversity", "bleu", "rouge"]

    result: Dict[str, Any] = {}
    extracted_text = _extract_all_text(slides)

    if "structure" in requested_metrics:
        result["structure_completeness"] = round(
            compute_structure_completeness(slides), 3
        )

    if "density" in requested_metrics:
        result["information_density"] = compute_information_density(slides)

    if "diversity" in requested_metrics:
        result["content_diversity"] = compute_content_diversity(slides)

    if "bleu" in requested_metrics and reference_text:
        result["bleu"] = compute_bleu(reference_text, extracted_text)

    if "rouge" in requested_metrics and reference_text:
        result["rouge_l"] = compute_rouge_l(reference_text, extracted_text)

    return result, extracted_text
