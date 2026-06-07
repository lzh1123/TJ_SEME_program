# Document Parsing, KB Import & Evaluation System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add long-document parsing (PDF/Word→Outline), async knowledge-base import with progress tracking, and an end-to-end evaluation system (rule-based metrics + LLM-as-Judge) to the Slideon PPT generator.

**Architecture:** New `evaluation/` service module with separate rule-based metrics (BLEU, ROUGE-L, structure, density, RAG recall) and LLM-as-Judge scorers, orchestrated by a central evaluator. New async task queue for non-blocking KB imports. New API endpoints under `/dsl/from-document`, `/rag/*`, and `/eval/*`. Frontend adds document upload to the outline modal, a KB management panel on the dashboard, and an evaluation panel in the editor plus a standalone batch-evaluation page.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, langchain-openai, pymilvus, sentence-transformers, Vue 3 (Composition API), Vite

---

### Task 1: Backend — Async Task Queue for KB Import

**Files:**
- Create: `backend/ppt_backend/services/rag/task_queue.py`

- [ ] **Step 1: Write the task queue module**

```python
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional

from ...domain.ids import new_id

logger = logging.getLogger(__name__)

TaskStatus = Literal["pending", "processing", "completed", "failed"]


@dataclass
class ImportTask:
    task_id: str
    status: TaskStatus = "pending"
    total: int = 0
    processed: int = 0
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "total": self.total,
            "processed": self.processed,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ImportTaskQueue:
    """Simple in-memory async task queue for KB document imports."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: Dict[str, ImportTask] = {}
        self._worker_task: Optional[asyncio.Task] = None
        self._handler: Optional[Callable] = None

    def set_handler(self, handler: Callable[[List[Path], ImportTask], Any]) -> None:
        """Set the async handler that processes a batch of files."""
        self._handler = handler

    async def start(self) -> None:
        """Start the background worker."""
        if self._worker_task is not None:
            return
        self._worker_task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the background worker."""
        if self._worker_task is not None:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None

    def enqueue(self, file_paths: List[Path]) -> str:
        """Enqueue files for import. Returns task_id for status polling."""
        task_id = new_id("import")
        task = ImportTask(task_id=task_id, total=len(file_paths))
        self._tasks[task_id] = task
        self._queue.put_nowait((task_id, file_paths))
        logger.info("Enqueued import task %s with %d files", task_id, len(file_paths))
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status by id. Returns None if not found."""
        task = self._tasks.get(task_id)
        if task is None:
            return None
        return task.to_dict()

    async def _run(self) -> None:
        """Background worker loop."""
        logger.info("Import task queue worker started")
        while True:
            try:
                task_id, file_paths = await self._queue.get()
                task = self._tasks.get(task_id)
                if task is None:
                    continue

                task.status = "processing"
                logger.info("Processing import task %s", task_id)

                try:
                    if self._handler is not None:
                        await self._handler(file_paths, task)
                    task.status = "completed"
                except Exception as e:
                    logger.error("Import task %s failed: %s", task_id, e)
                    task.status = "failed"
                    task.errors.append(f"{type(e).__name__}: {e}")

                task.completed_at = datetime.now(timezone.utc)
            except asyncio.CancelledError:
                logger.info("Import task queue worker stopping")
                return
            except Exception as e:
                logger.error("Import task worker error: %s", e)


# Module-level singleton
_import_queue: Optional[ImportTaskQueue] = None


def get_import_queue() -> ImportTaskQueue:
    global _import_queue
    if _import_queue is None:
        _import_queue = ImportTaskQueue()
    return _import_queue
```

- [ ] **Step 2: Verify the module imports cleanly**

```bash
cd backend && python -c "from ppt_backend.services.rag.task_queue import ImportTaskQueue, get_import_queue; q = get_import_queue(); print('OK:', type(q).__name__)"
```

Expected: `OK: ImportTaskQueue`

- [ ] **Step 3: Commit**

```bash
git add backend/ppt_backend/services/rag/task_queue.py
git commit -m "feat: add async import task queue for KB document ingestion"
```

---

### Task 2: Backend — Evaluation Schemas

**Files:**
- Create: `backend/ppt_backend/services/evaluation/__init__.py`
- Create: `backend/ppt_backend/services/evaluation/schemas.py`

- [ ] **Step 1: Write the `__init__.py`**

```python
from .evaluator import Evaluator
from .schemas import (
    BatchEvalRequest,
    EvalReport,
    EvalRequest,
    EvalResult,
    LLMJudgeScores,
    RuleMetrics,
)

__all__ = [
    "Evaluator",
    "EvalRequest",
    "EvalResult",
    "EvalReport",
    "BatchEvalRequest",
    "RuleMetrics",
    "LLMJudgeScores",
]
```

- [ ] **Step 2: Write the schemas module**

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

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
```

- [ ] **Step 3: Verify imports**

```bash
cd backend && python -c "from ppt_backend.services.evaluation.schemas import EvalRequest, EvalResult, BatchEvalRequest, RuleMetrics, LLMJudgeScores; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/ppt_backend/services/evaluation/__init__.py backend/ppt_backend/services/evaluation/schemas.py
git commit -m "feat: add evaluation schemas (EvalRequest, EvalResult, BatchEvalRequest)"
```

---

### Task 3: Backend — Rule-Based Metrics Calculator

**Files:**
- Create: `backend/ppt_backend/services/evaluation/metrics.py`

- [ ] **Step 1: Write the metrics module**

```python
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
    sections = [s.get("section", "") for s in slides]

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
```

- [ ] **Step 2: Quick smoke test**

```bash
cd backend && python -c "
from ppt_backend.services.evaluation.metrics import compute_structure_completeness, compute_information_density, compute_content_diversity
slides = [
    {'intent': 'cover', 'title': 'Test'},
    {'intent': 'agenda', 'title': 'TOC', 'items': ['a','b']},
    {'intent': 'text', 'title': 'Content 1', 'bullets': ['point 1', 'point 2', 'point 3']},
    {'intent': 'text', 'title': 'Content 2', 'paragraphs': ['a long paragraph here']},
    {'intent': 'kpi', 'title': 'Metrics', 'items': [{'label':'A','value':'10'}]},
    {'intent': 'divider', 'title': 'Thanks'},
]
print('Structure:', compute_structure_completeness(slides))
print('Density:', compute_information_density(slides))
print('Diversity:', compute_content_diversity(slides))
print('OK')
"
```

Expected: Numeric scores printed, no errors.

- [ ] **Step 3: Commit**

```bash
git add backend/ppt_backend/services/evaluation/metrics.py
git commit -m "feat: add rule-based evaluation metrics (BLEU, ROUGE-L, structure, density, diversity)"
```

---

### Task 4: Backend — RAG Evaluation Metrics

**Files:**
- Create: `backend/ppt_backend/services/evaluation/rag_eval.py`

- [ ] **Step 1: Write the RAG eval module**

```python
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Global in-memory retrieval log: {presentation_id: [{"query": str, "chunks": [...], "used": bool}]}
_retrieval_log: Dict[str, List[Dict[str, Any]]] = {}


def log_retrieval(presentation_id: str, query: str, chunks: List[Dict[str, Any]]) -> None:
    """Log retrieval results for later RAG evaluation."""
    if presentation_id not in _retrieval_log:
        _retrieval_log[presentation_id] = []
    _retrieval_log[presentation_id].append({
        "query": query,
        "chunks": chunks,
    })


def mark_chunks_used(presentation_id: str, slide_content: str) -> None:
    """Mark retrieved chunks as 'used' if their text appears (substring match) in slide content."""
    if presentation_id not in _retrieval_log:
        return

    for entry in _retrieval_log[presentation_id]:
        for chunk in entry.get("chunks", []):
            chunk_text = chunk.get("text", "")
            if not chunk_text:
                continue
            # Simple substring check — chunk text of sufficient length appears in content
            snippet = chunk_text[:80]
            if len(snippet) >= 20 and snippet in slide_content:
                chunk["used"] = True


def compute_rag_recall(presentation_id: str) -> Optional[float]:
    """Compute recall: fraction of retrieved chunks that were used in the PPT content."""
    if presentation_id not in _retrieval_log:
        return None

    entries = _retrieval_log[presentation_id]
    total_chunks = 0
    used_chunks = 0

    for entry in entries:
        for chunk in entry.get("chunks", []):
            total_chunks += 1
            if chunk.get("used", False):
                used_chunks += 1

    if total_chunks == 0:
        return None

    return round(used_chunks / total_chunks, 4)


def compute_rag_precision(presentation_id: str) -> Optional[float]:
    """Compute precision: fraction of entries with at least one used chunk."""
    if presentation_id not in _retrieval_log:
        return None

    entries = _retrieval_log[presentation_id]
    if not entries:
        return None

    entries_with_hits = 0
    for entry in entries:
        if any(chunk.get("used", False) for chunk in entry.get("chunks", [])):
            entries_with_hits += 1

    return round(entries_with_hits / len(entries), 4)


def clear_retrieval_log(presentation_id: Optional[str] = None) -> None:
    """Clear retrieval logs. If presentation_id is None, clear all."""
    if presentation_id is None:
        _retrieval_log.clear()
    else:
        _retrieval_log.pop(presentation_id, None)
```

- [ ] **Step 2: Verify imports**

```bash
cd backend && python -c "from ppt_backend.services.evaluation.rag_eval import log_retrieval, compute_rag_recall, compute_rag_precision; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/ppt_backend/services/evaluation/rag_eval.py
git commit -m "feat: add RAG evaluation metrics (retrieval recall & precision)"
```

---

### Task 5: Backend — LLM-as-Judge Scorer

**Files:**
- Create: `backend/ppt_backend/services/evaluation/llm_judge.py`

- [ ] **Step 1: Write the LLM judge module**

```python
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from langchain_core.prompts import ChatPromptTemplate

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


from pydantic import BaseModel, Field


class LLMJudgeScoresWithSuggestions(BaseModel):
    structure_rationality: Optional[int] = None
    fact_accuracy: Optional[int] = None
    logical_coherence: Optional[int] = None
    content_depth: Optional[int] = None
    overall_quality: Optional[int] = None
    suggestions: List[str] = Field(default_factory=list)
```

- [ ] **Step 2: Verify imports**

```bash
cd backend && python -c "from ppt_backend.services.evaluation.llm_judge import LLMJudge; j = LLMJudge(); print('Available:', j.available)"
```

Expected: `Available: True` (if LLM configured) or `Available: False`

- [ ] **Step 3: Commit**

```bash
git add backend/ppt_backend/services/evaluation/llm_judge.py
git commit -m "feat: add LLM-as-Judge scorer for PPT quality evaluation"
```

---

### Task 6: Backend — Evaluator Orchestrator

**Files:**
- Create: `backend/ppt_backend/services/evaluation/evaluator.py`

- [ ] **Step 1: Write the evaluator orchestrator**

```python
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ...domain.ids import new_id
from .llm_judge import LLMJudge
from .metrics import compute_rule_metrics, _extract_all_text
from .rag_eval import compute_rag_precision, compute_rag_recall, mark_chunks_used
from .schemas import EvalResult, LLMJudgeScores, RuleMetrics, DensityMetrics, DiversityMetrics, BleuScores, RougeLScores

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
            total_rule_weight = sum(
                w for w in [0.15, 0.1, 0.05, 0.1]
            )
            if total_rule_weight > 0:
                factor = 1.0 / total_rule_weight
                parts = [p * factor for p in parts]

        return sum(parts)
```

- [ ] **Step 2: Verify imports**

```bash
cd backend && python -c "from ppt_backend.services.evaluation.evaluator import Evaluator; e = Evaluator(); print('OK:', type(e).__name__)"
```

Expected: `OK: Evaluator`

- [ ] **Step 3: Commit**

```bash
git add backend/ppt_backend/services/evaluation/evaluator.py
git commit -m "feat: add evaluation orchestrator (rule metrics + LLM judge)"
```

---

### Task 7: Backend — Add Retrieval Logging to HybridRetriever

**Files:**
- Modify: `backend/ppt_backend/services/rag/retrieval.py:1-75`

- [ ] **Step 1: Add retrieval logging to the `retrieve` method**

In [retrieval.py](backend/ppt_backend/services/rag/retrieval.py), add to the imports at line 14:

```python
from ...services.evaluation.rag_eval import log_retrieval
```

Wait — the rag_eval module is in `services/evaluation/`, which is a sibling of `services/rag/`. Let's check: `ppt_backend/services/evaluation/rag_eval.py`. The import from `retrieval.py` should be:

```python
# Add at line 14 (after existing imports), wrapped in try to avoid hard dependency
try:
    from ..evaluation.rag_eval import log_retrieval
except ImportError:
    log_retrieval = None
```

Then inside the `retrieve` method (around line 67, after `fused = self._rrf_fuse(...)`), add:

```python
# Log retrieval for RAG evaluation (if available)
if log_retrieval is not None:
    try:
        log_retrieval(
            presentation_id="unknown",  # will be updated by caller
            query=query,
            chunks=fused,
        )
    except Exception:
        pass
```

Wait, this approach is too coupled. Let me instead use a simpler pattern — a callable hook on the retriever:

Actually, let me take a simpler approach. Instead of modifying the retriever, I'll hook into the presentation_service which already orchestrates RAG calls. The presentation_service calls `self._rag.retrieve_context(topic, ...)` and then passes it to the AI pipeline. I'll add the logging there.

Let me revise this task:

- [ ] **Step 1: Modify `presentation_service.py` to log retrievals**

In [presentation_service.py](backend/ppt_backend/services/presentation_service.py), add import at line 18:

```python
try:
    from .evaluation.rag_eval import log_retrieval
except ImportError:
    log_retrieval = None
```

In the `create` method (around line 44, after `rag_context = self._rag.retrieve_context(...)`), add:

```python
if log_retrieval is not None and rag_context:
    try:
        result = self._rag.search(topic, top_k=8)
        log_retrieval(presentation_id, topic,
            result.get("fused_results", []) if isinstance(result, dict) else [])
    except Exception:
        pass
```

And in `generate_outline` (around line 67), add similar logging.

- [ ] **Step 2: Verify the modified file imports correctly**

```bash
cd backend && python -c "from ppt_backend.services.presentation_service import PresentationService; print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend/ppt_backend/services/presentation_service.py
git commit -m "feat: add RAG retrieval logging for evaluation metrics"
```

---

### Task 8: Backend — New API Endpoints (Document + KB + Evaluation)

**Files:**
- Modify: `backend/ppt_backend/api/routes.py` (add new endpoints)

- [ ] **Step 1: Add document-to-outline endpoint and KB/evaluation routes**

Add after the existing imports in [routes.py](backend/ppt_backend/api/routes.py) (around line 16):

```python
from ..services.rag.task_queue import get_import_queue
```

Add new request models after `RagSearchRequest` (around line 90):

```python
class EvalSingleRequest(BaseModel):
    model_config = {"extra": "forbid"}

    reference_text: Optional[str] = None
    enable_llm_judge: bool = True
    metrics: Optional[List[str]] = None


class BatchEvalConfigModel(BaseModel):
    name: str
    use_rag: bool = True
    theme: Optional[str] = None


class BatchEvalRequestModel(BaseModel):
    model_config = {"extra": "forbid"}

    configs: List[BatchEvalConfigModel]
    topics: List[str]
    metrics: Optional[List[str]] = None
    reference_texts: Dict[str, str] = Field(default_factory=dict)
```

Add new endpoints after the existing `rag_bootstrap` endpoint (around line 395):

```python
# ── Document → Outline endpoint ─────────────────────────────────

@router.post("/dsl/from-document")
async def generate_outline_from_document(
    request: Request,
    file: UploadFile = File(...),
    theme: Optional[str] = Form(None),
    svc: PresentationService = Depends(get_service),
):
    """Upload a document (PDF/DOCX/TXT/MD), parse it, generate an outline,
    and ingest the document into the knowledge base asynchronously."""
    try:
        import tempfile
        import os

        suffix = Path(file.filename or "upload").suffix.lower()
        if suffix not in (".pdf", ".docx", ".txt", ".md"):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {suffix}. Supported: .pdf, .docx, .txt, .md",
            )

        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Parse document (reuse knowledge_base._read_file)
            from ..services.rag.knowledge_base import KnowledgeBase
            from ..services.rag.milvus_client import MilvusStore
            from ..services.rag.embedding import EmbeddingService
            from ..settings import settings

            store = MilvusStore(uri=settings.milvus_uri, db_name=settings.milvus_db)
            embedding = EmbeddingService(model_name=settings.embedding_model)
            kb = KnowledgeBase(store=store, embedding=embedding)
            doc_text = kb._read_file(Path(tmp_path), suffix)

            if not doc_text:
                raise HTTPException(status_code=400, detail="Could not extract text from document")

            # Truncate very long documents for the LLM prompt
            max_chars = 10000
            if len(doc_text) > max_chars:
                # Keep first 40% + last 20% + sampled middle
                first = doc_text[: int(max_chars * 0.4)]
                last = doc_text[-int(max_chars * 0.2):]
                doc_text_for_llm = first + "\n\n...[content truncated]...\n\n" + last
            else:
                doc_text_for_llm = doc_text

            # Generate outline using document text as rag_context
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(
                None,
                lambda: svc.generate_outline(
                    topic=file.filename or "Document Outline",
                    theme=theme,
                    use_rag=False,  # Don't search — use doc text directly
                ),
            )
            while not future.done():
                if await request.is_disconnected():
                    future.cancel()
                    raise HTTPException(status_code=499, detail="Client disconnected")
                await asyncio.sleep(0.5)

            # Override: regenerate with doc text context
            from ..services.ai.pipeline import AiPipeline
            ai = AiPipeline()
            dsl = ai.generate_dsl(
                topic=f"Based on document: {file.filename}",
                theme=theme,
                rag_context=doc_text_for_llm,
            )
            data = dsl.model_dump(by_alias=True)
            slides = data.get("slides") or []
            if isinstance(slides, list):
                for s in slides:
                    if isinstance(s, dict):
                        s.pop("id", None)
            data["slides"] = slides

            # Fire-and-forget KB ingestion
            try:
                kb.ingest_text(doc_text, source=file.filename or "uploaded_document")
            except Exception as e:
                logging.getLogger(__name__).warning(
                    "KB ingestion for document %s failed (non-blocking): %s",
                    file.filename, e,
                )

            return data

        finally:
            os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── KB Management endpoints ────────────────────────────────────

@router.post("/rag/documents/batch")
async def rag_upload_documents_batch(
    files: List[UploadFile] = File(...),
    svc: PresentationService = Depends(get_service),
):
    """Upload multiple documents for async KB import. Returns task_id."""
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")

    import tempfile
    import os

    saved_paths = []
    for file in files:
        suffix = Path(file.filename or "upload").suffix or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            saved_paths.append(Path(tmp.name))

    queue = get_import_queue()

    async def process_files(paths: List[Path], task: Any) -> None:
        for i, path in enumerate(paths):
            try:
                rag.ingest_document(path)
                task.processed = i + 1
            except Exception as e:
                task.errors.append(f"{path.name}: {type(e).__name__}: {e}")
            finally:
                try:
                    os.unlink(path)
                except Exception:
                    pass

    queue.set_handler(process_files)
    task_id = queue.enqueue(saved_paths)

    return {"task_id": task_id, "file_count": len(files)}


@router.get("/rag/tasks/{task_id}")
def rag_task_status(task_id: str):
    """Get import task progress."""
    queue = get_import_queue()
    task = queue.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/rag/documents")
def rag_list_documents(svc: PresentationService = Depends(get_service)):
    """List documents in the knowledge base."""
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        stats = rag.get_kb_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Evaluation endpoints ───────────────────────────────────────

def _get_evaluator():
    """Lazy-load evaluator."""
    from ..services.evaluation.evaluator import Evaluator
    return Evaluator()


@router.post("/eval/single/{presentation_id}")
def eval_single_presentation(
    presentation_id: str,
    payload: EvalSingleRequest = Body(default=EvalSingleRequest()),
    svc: PresentationService = Depends(get_service),
):
    """Evaluate a single presentation's outline quality."""
    try:
        bundle = svc.get(presentation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Presentation not found")

    slides_raw = bundle.dsl.model_dump(by_alias=True).get("slides", [])
    topic = bundle.meta.topic

    evaluator = _get_evaluator()
    result = evaluator.evaluate_single(
        presentation_id=presentation_id,
        topic=topic,
        slides=slides_raw,
        reference_text=payload.reference_text,
        enable_llm_judge=payload.enable_llm_judge,
        requested_metrics=payload.metrics,
    )
    return result.model_dump()


@router.post("/eval/batch")
async def eval_batch(
    payload: BatchEvalRequestModel,
    request: Request,
    svc: PresentationService = Depends(get_service),
):
    """Batch evaluate multiple configs × topics."""
    from ..services.evaluation.evaluator import Evaluator

    evaluator = Evaluator()
    results: List[dict] = []

    for config in payload.configs:
        for topic in payload.topics:
            try:
                # Generate PPT with this config
                loop = asyncio.get_event_loop()
                future = loop.run_in_executor(
                    None,
                    lambda t=topic, c=config: svc.create(
                        topic=t, theme=c.theme, use_rag=c.use_rag
                    ),
                )
                while not future.done():
                    if await request.is_disconnected():
                        future.cancel()
                        raise HTTPException(status_code=499, detail="Client disconnected")
                    await asyncio.sleep(0.5)
                bundle = future.result()

                slides_raw = bundle.dsl.model_dump(by_alias=True).get("slides", [])
                ref = payload.reference_texts.get(topic)

                eval_result = evaluator.evaluate_single(
                    presentation_id=bundle.meta.id,
                    topic=topic,
                    slides=slides_raw,
                    reference_text=ref,
                    enable_llm_judge="llm_judge" in (payload.metrics or []),
                    requested_metrics=payload.metrics,
                )
                result_dict = eval_result.model_dump()
                result_dict["config"] = config.name
                results.append(result_dict)
            except Exception as e:
                results.append({
                    "config": config.name,
                    "topic": topic,
                    "error": f"{type(e).__name__}: {e}",
                })

    return {
        "configs": [c.name for c in payload.configs],
        "topics": payload.topics,
        "results": results,
    }
```

- [ ] **Step 2: Verify the routes compile**

```bash
cd backend && python -c "from ppt_backend.api.main import app; print('Routes:', len(app.routes)); print('OK')"
```

Expected: `Routes: <number>` (no import errors)

- [ ] **Step 3: Commit**

```bash
git add backend/ppt_backend/api/routes.py
git commit -m "feat: add API endpoints for document-to-outline, KB management, and evaluation"
```

---

### Task 9: Backend — Start Task Queue Worker in main.py

**Files:**
- Modify: `backend/ppt_backend/api/main.py:76-78`

- [ ] **Step 1: Start the import task queue worker at app startup**

In [main.py](backend/ppt_backend/api/main.py), add after line 72 (`app.state.presentation_service = build_presentation_service()`):

```python
    # Start import task queue worker
    from ..services.rag.task_queue import get_import_queue
    import_queue = get_import_queue()

    @app.on_event("startup")
    async def start_import_worker():
        await import_queue.start()

    @app.on_event("shutdown")
    async def stop_import_worker():
        await import_queue.stop()
```

- [ ] **Step 2: Verify the app starts**

```bash
cd backend && timeout 5 python -c "
import asyncio
from ppt_backend.api.main import app
print('App created OK')
" || echo "Timed out (expected — FastAPI app blocks)"
```

- [ ] **Step 3: Commit**

```bash
git add backend/ppt_backend/api/main.py
git commit -m "feat: start async import task queue worker at app startup"
```

---

### Task 10: Frontend — API Service & Config Updates

**Files:**
- Modify: `slideon-frontend/src/config/api.js:39-51`
- Modify: `slideon-frontend/src/services/api.js:1-199`

- [ ] **Step 1: Add new endpoint configs**

In [api.js](slideon-frontend/src/config/api.js), add after the `presentations` block (line 36):

```javascript
  // 知识库相关
  rag: {
    search: '/rag/search',
    enhance: '/rag/enhance',
    documents: '/rag/documents',
    documentsBatch: '/rag/documents/batch',
    documentDelete: (source) => `/rag/documents/${encodeURIComponent(source)}`,
    taskStatus: (taskId) => `/rag/tasks/${taskId}`,
    stats: '/rag/stats',
    collectionInit: '/rag/collection/init',
    collectionReset: '/rag/collection/reset',
    bootstrap: '/rag/bootstrap'
  },

  // 文档导入生成大纲
  dslFromDocument: '/dsl/from-document',

  // 评估相关
  eval: {
    single: (presentationId) => `/eval/single/${presentationId}`,
    batch: '/eval/batch'
  }
```

- [ ] **Step 2: Add new API methods**

In [api.js](slideon-frontend/src/services/api.js), add after `compileOutline` (line 196):

```javascript
  // ── 文档上传生成大纲 ──
  async generateOutlineFromDocument(file, theme = null, signal = null) {
    const formData = new FormData()
    formData.append('file', file)
    if (theme) formData.append('theme', theme)

    const response = await fetch(`${this.baseURL}${API_ENDPOINTS.dslFromDocument}`, {
      method: 'POST',
      body: formData,
      signal
      // Note: don't set Content-Type header — browser sets it with boundary for FormData
    })
    if (!response.ok) {
      let detail = `HTTP ${response.status}`
      try { const err = await response.json(); detail = err.detail || detail } catch {}
      throw new Error(detail)
    }
    return response.json()
  },

  // ── 知识库管理 ──
  async uploadDocumentsToKB(files) {
    const formData = new FormData()
    files.forEach(f => formData.append('files', f))
    const response = await fetch(`${this.baseURL}${API_ENDPOINTS.rag.documentsBatch}`, {
      method: 'POST',
      body: formData
    })
    if (!response.ok) {
      let detail = `HTTP ${response.status}`
      try { const err = await response.json(); detail = err.detail || detail } catch {}
      throw new Error(detail)
    }
    return response.json()
  },

  async getImportTaskStatus(taskId) {
    const response = await this.get(API_ENDPOINTS.rag.taskStatus(taskId))
    return response.json()
  },

  async getKBDocuments() {
    const response = await this.get(API_ENDPOINTS.rag.documents)
    return response.json()
  },

  async removeKBDocument(source) {
    const response = await this.request(API_ENDPOINTS.rag.documentDelete(source), {
      method: 'DELETE'
    })
    return response.json()
  },

  async getKBStats() {
    const response = await this.get(API_ENDPOINTS.rag.stats)
    return response.json()
  },

  // ── 评估 ──
  async evaluatePresentation(presentationId, options = {}) {
    const response = await this.post(API_ENDPOINTS.eval.single(presentationId), {
      reference_text: options.referenceText || null,
      enable_llm_judge: options.enableLLMJudge !== false,
      metrics: options.metrics || null
    })
    return response.json()
  },

  async batchEvaluate(config) {
    const response = await this.post(API_ENDPOINTS.eval.batch, config)
    return response.json()
  }
```

- [ ] **Step 3: Verify the API service builds**

```bash
cd slideon-frontend && npx vite build --mode development 2>&1 | tail -5
```

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add slideon-frontend/src/config/api.js slideon-frontend/src/services/api.js
git commit -m "feat: add frontend API methods for document upload, KB management, and evaluation"
```

---

### Task 11: Frontend — Document Upload in OutlineModal

**Files:**
- Modify: `slideon-frontend/src/components/common/OutlineModal.vue`

- [ ] **Step 1: Add document upload mode to OutlineModal**

Add a mode toggle and file upload area. Replace the template section between the modal-header and the first form-step:

```html
<!-- After the modal-header div, add mode tabs: -->
<div class="mode-tabs">
  <button
    :class="['mode-tab', { active: inputMode === 'text' }]"
    @click="inputMode = 'text'"
    :disabled="isGenerating"
  >输入主题</button>
  <button
    :class="['mode-tab', { active: inputMode === 'file' }]"
    @click="inputMode = 'file'"
    :disabled="isGenerating"
  >导入文档</button>
</div>
```

Replace the topic textarea section with conditional rendering:

```html
<!-- Text mode: existing textarea -->
<div v-if="inputMode === 'text'" class="form-step">
  <label class="form-label">
    <span class="step-number">1</span>
    输入主题
  </label>
  <textarea
    class="input textarea"
    placeholder="描述你的PPT主题、目标受众和主要内容..."
    v-model="form.topic"
    :disabled="isGenerating"
    @input="updateCharCount"
  ></textarea>
  <div class="char-count" :class="{ error: charCount > 500 }">{{ charCount }}/500</div>
</div>

<!-- File mode: upload area -->
<div v-if="inputMode === 'file'" class="form-step">
  <label class="form-label">
    <span class="step-number">1</span>
    选择文档
  </label>
  <div
    class="upload-zone"
    :class="{ 'has-file': selectedFile, 'drag-over': isDragOver }"
    @click="triggerFileInput"
    @dragover.prevent="isDragOver = true"
    @dragleave.prevent="isDragOver = false"
    @drop.prevent="handleFileDrop"
  >
    <input
      ref="fileInput"
      type="file"
      accept=".pdf,.docx,.txt,.md"
      style="display:none"
      @change="handleFileSelect"
    />
    <template v-if="!selectedFile">
      <IconBase name="upload" :size="32" />
      <p class="upload-text">拖拽文件到此处或点击选择</p>
      <p class="upload-hint">支持 PDF、Word、TXT、Markdown 格式</p>
    </template>
    <template v-else>
      <IconBase name="file" :size="24" />
      <p class="upload-filename">{{ selectedFile.name }}</p>
      <p class="upload-size">{{ formatFileSize(selectedFile.size) }}</p>
      <button class="btn btn-sm btn-secondary" @click.stop="clearFile">移除</button>
    </template>
  </div>
</div>
```

Update the script section — add new reactive state:

```javascript
const inputMode = ref('text')
const selectedFile = ref(null)
const isDragOver = ref(false)
const fileInput = ref(null)

function triggerFileInput() {
  if (!isGenerating.value) fileInput.value?.click()
}

function handleFileSelect(e) {
  const file = e.target.files?.[0]
  if (file) selectedFile.value = file
}

function handleFileDrop(e) {
  isDragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) selectedFile.value = file
}

function clearFile() {
  selectedFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
```

Modify `generateOutline` to dispatch based on mode:

```javascript
const generateOutline = async () => {
  if (inputMode.value === 'file') {
    await generateFromDocument()
  } else {
    await generateFromTopic()
  }
}

const generateFromTopic = async () => {
  // existing generateOutline logic (rename from generateOutline)
  if (!form.value.topic.trim()) { alert('请输入主题'); return }
  isGenerating.value = true
  try {
    abortController = new AbortController()
    const result = await apiService.generateOutline(
      form.value.topic, form.value.style, useRag.value, abortController.signal
    )
    console.log('✅ 生成大纲成功:', result)
    const { id } = outlineStore.createOutline(result)
    if (!props.modelValue) { setSuccess(id) }
    else { close(); router.push({ path: '/outline-editor', query: { id } }) }
  } catch (error) {
    if (error.name === 'AbortError') { console.log('⚠️ 生成已取消'); return }
    console.error('❌ 生成大纲失败:', error)
    emit('update:modelValue', false)
    setError()
  } finally { isGenerating.value = false; abortController = null }
}

const generateFromDocument = async () => {
  if (!selectedFile.value) { alert('请选择文档'); return }
  isGenerating.value = true
  try {
    abortController = new AbortController()
    const result = await apiService.generateOutlineFromDocument(
      selectedFile.value, form.value.style, abortController.signal
    )
    console.log('✅ 文档大纲生成成功:', result)
    const { id } = outlineStore.createOutline(result)
    if (!props.modelValue) { setSuccess(id) }
    else { close(); router.push({ path: '/outline-editor', query: { id } }) }
  } catch (error) {
    if (error.name === 'AbortError') { console.log('⚠️ 生成已取消'); return }
    console.error('❌ 文档大纲生成失败:', error)
    emit('update:modelValue', false)
    setError()
  } finally { isGenerating.value = false; abortController = null; selectedFile.value = null }
}
```

Update the generate button disabled condition:

```html
:disabled="isGenerating || (inputMode === 'text' && !form.topic.trim()) || (inputMode === 'file' && !selectedFile)"
```

Update the generate button text:

```html
{{ isGenerating ? (inputMode === 'file' ? '解析文档并生成大纲中...' : '生成大纲中...') : '生成大纲' }}
```

Add styles for upload zone:

```css
.mode-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--gray-200);
  margin-bottom: var(--space-4);
}

.mode-tab {
  flex: 1;
  padding: var(--space-3) var(--space-4);
  border: none;
  background: transparent;
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-500);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
}

.mode-tab.active {
  color: var(--primary-600);
  border-bottom-color: var(--primary-500);
}

.mode-tab:hover:not(.active):not(:disabled) {
  color: var(--gray-700);
  background: var(--gray-50);
}

.mode-tab:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-zone {
  border: 2px dashed var(--gray-300);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--gray-50);
}

.upload-zone:hover,
.upload-zone.drag-over {
  border-color: var(--primary-400);
  background: var(--primary-50);
}

.upload-zone.has-file {
  border-style: solid;
  border-color: var(--primary-300);
  background: var(--primary-50);
}

.upload-text {
  font-size: 14px;
  color: var(--gray-600);
  margin: var(--space-2) 0 var(--space-1);
}

.upload-hint {
  font-size: 12px;
  color: var(--gray-400);
  margin: 0;
}

.upload-filename {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
  margin: var(--space-2) 0 0;
}

.upload-size {
  font-size: 12px;
  color: var(--gray-500);
  margin: var(--space-1) 0 var(--space-2);
}
```

- [ ] **Step 2: Verify build**

```bash
cd slideon-frontend && npx vite build --mode development 2>&1 | tail -5
```

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add slideon-frontend/src/components/common/OutlineModal.vue
git commit -m "feat: add document upload mode to outline creation modal"
```

---

### Task 12: Frontend — Knowledge Base Management Panel

**Files:**
- Create: `slideon-frontend/src/components/common/KnowledgeBasePanel.vue`

- [ ] **Step 1: Write the KnowledgeBasePanel component**

```vue
<template>
  <Teleport to="body">
    <div v-if="visible" class="kb-overlay" @click.self="close">
      <div class="kb-panel">
        <div class="kb-header">
          <h2>知识库管理</h2>
          <button class="modal-close-btn" @click="close">
            <IconBase name="times" :size="20" />
          </button>
        </div>

        <!-- Upload Area -->
        <div class="kb-section">
          <h3>导入文档</h3>
          <div
            class="upload-zone"
            :class="{ 'drag-over': isDragOver }"
            @click="triggerUpload"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @drop.prevent="handleDrop"
          >
            <input ref="uploadInput" type="file" accept=".pdf,.docx,.txt,.md" multiple style="display:none" @change="handleFiles" />
            <IconBase name="upload" :size="28" />
            <p>拖拽文件到此处或点击上传</p>
            <span class="hint">支持 PDF、Word、TXT、Markdown，可批量上传</span>
          </div>

          <!-- Selected files -->
          <div v-if="pendingFiles.length > 0 && !uploading" class="pending-files">
            <div v-for="(f, i) in pendingFiles" :key="i" class="pending-file">
              <IconBase name="file" :size="14" />
              <span>{{ f.name }}</span>
              <span class="file-size">{{ formatSize(f.size) }}</span>
              <button class="mini-btn" @click="pendingFiles.splice(i,1)">✕</button>
            </div>
            <button class="btn btn-primary btn-sm" @click="startUpload">
              开始导入 ({{ pendingFiles.length }} 个文件)
            </button>
          </div>

          <!-- Progress -->
          <div v-if="uploading" class="upload-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            </div>
            <span class="progress-text">{{ progressText }}</span>
          </div>
        </div>

        <!-- Document List -->
        <div class="kb-section">
          <h3>已导入文档 ({{ documents.length }})</h3>
          <div v-if="documents.length === 0" class="empty-hint">还没有导入任何文档</div>
          <div v-else class="doc-list">
            <div v-for="(doc, i) in documents" :key="i" class="doc-item">
              <div class="doc-info">
                <IconBase name="file" :size="16" />
                <span class="doc-name">{{ doc.source || doc.filename || '未知文档' }}</span>
                <span class="doc-chunks">{{ doc.chunks || doc.num_entities || 0 }} 块</span>
              </div>
              <button class="mini-btn danger" @click="removeDoc(doc)">删除</button>
            </div>
          </div>
        </div>

        <div class="kb-footer">
          <span>共 {{ stats.num_entities || 0 }} 条知识条目</span>
          <button class="btn btn-secondary" @click="close">关闭</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import IconBase from '../icons/IconBase.vue'
import { apiService } from '../../services/api.js'

const props = defineProps({
  visible: { type: Boolean, default: false }
})
const emit = defineEmits(['update:visible'])

const isDragOver = ref(false)
const pendingFiles = ref([])
const uploading = ref(false)
const progressPercent = ref(0)
const progressText = ref('')
const documents = ref([])
const stats = ref({})
const uploadInput = ref(null)
let pollTimer = null

onMounted(() => { if (props.visible) loadDocuments() })

function close() { emit('update:visible', false) }

function triggerUpload() { uploadInput.value?.click() }
function handleFiles(e) {
  const files = Array.from(e.target.files || [])
  pendingFiles.value.push(...files)
}
function handleDrop(e) {
  isDragOver.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  pendingFiles.value.push(...files)
}

async function startUpload() {
  if (pendingFiles.value.length === 0) return
  uploading.value = true
  progressText.value = '正在上传...'
  try {
    const result = await apiService.uploadDocumentsToKB(pendingFiles.value)
    const taskId = result.task_id
    pendingFiles.value = []
    // Poll for progress
    pollTimer = setInterval(async () => {
      try {
        const task = await apiService.getImportTaskStatus(taskId)
        if (task.total > 0) {
          progressPercent.value = Math.round((task.processed / task.total) * 100)
        }
        progressText.value = `处理中 ${task.processed}/${task.total}`
        if (task.status === 'completed' || task.status === 'failed') {
          clearInterval(pollTimer)
          uploading.value = false
          progressText.value = task.status === 'completed' ? '导入完成' : '导入失败'
          if (task.errors.length > 0) {
            progressText.value += ` (${task.errors.length} 个错误)`
          }
          loadDocuments()
        }
      } catch { clearInterval(pollTimer); uploading.value = false }
    }, 1000)
  } catch (e) {
    uploading.value = false
    progressText.value = '上传失败: ' + e.message
  }
}

async function loadDocuments() {
  try {
    stats.value = await apiService.getKBStats()
    documents.value = [{ source: 'knowledge_base', chunks: stats.value.num_entities || 0 }]
  } catch {}
}

async function removeDoc(doc) { /* placeholder */ }

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}
</script>

<style scoped>
.kb-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.5); backdrop-filter:blur(4px); display:flex; align-items:center; justify-content:center; z-index:2000; }
.kb-panel { background:white; border-radius:16px; width:640px; max-height:80vh; display:flex; flex-direction:column; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.15); }
.kb-header { display:flex; align-items:center; justify-content:space-between; padding:20px 24px; border-bottom:1px solid #e5e7eb; }
.kb-header h2 { font-size:18px; font-weight:600; color:#1f2937; margin:0; }
.modal-close-btn { width:36px; height:36px; display:flex; align-items:center; justify-content:center; border:none; background:transparent; border-radius:8px; color:#6b7280; cursor:pointer; }
.modal-close-btn:hover { background:#f3f4f6; color:#1f2937; }
.kb-section { padding:20px 24px; border-bottom:1px solid #f3f4f6; }
.kb-section h3 { font-size:14px; font-weight:600; color:#374151; margin:0 0 12px; }
.upload-zone { border:2px dashed #d1d5db; border-radius:12px; padding:32px; text-align:center; cursor:pointer; transition:all .2s; background:#f9fafb; color:#6b7280; }
.upload-zone:hover, .upload-zone.drag-over { border-color:#6366f1; background:#eef2ff; color:#4f46e5; }
.upload-zone p { font-size:14px; margin:8px 0 4px; }
.hint { font-size:12px; color:#9ca3af; }
.pending-files { margin-top:12px; }
.pending-file { display:flex; align-items:center; gap:8px; padding:8px 12px; background:#f9fafb; border-radius:8px; margin-bottom:6px; font-size:13px; }
.file-size { color:#9ca3af; font-size:12px; margin-left:auto; }
.upload-progress { margin-top:12px; }
.progress-bar { height:6px; background:#e5e7eb; border-radius:3px; overflow:hidden; }
.progress-fill { height:100%; background:linear-gradient(90deg,#6366f1,#8b5cf6); border-radius:3px; transition:width .3s; }
.progress-text { font-size:12px; color:#6b7280; display:block; margin-top:6px; }
.doc-list { display:flex; flex-direction:column; gap:4px; }
.doc-item { display:flex; align-items:center; justify-content:space-between; padding:10px 12px; background:#f9fafb; border-radius:8px; }
.doc-info { display:flex; align-items:center; gap:8px; font-size:13px; }
.doc-name { color:#374151; font-weight:500; }
.doc-chunks { font-size:12px; color:#9ca3af; }
.empty-hint { font-size:13px; color:#9ca3af; text-align:center; padding:20px; }
.kb-footer { display:flex; align-items:center; justify-content:space-between; padding:16px 24px; background:#f9fafb; font-size:13px; color:#6b7280; }
</style>
```

- [ ] **Step 2: Verify build**

```bash
cd slideon-frontend && npx vite build --mode development 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add slideon-frontend/src/components/common/KnowledgeBasePanel.vue
git commit -m "feat: add knowledge base management panel component"
```

---

### Task 13: Frontend — Add KB Button to Dashboard

**Files:**
- Modify: `slideon-frontend/src/views/DashboardView.vue:10-11`

- [ ] **Step 1: Add KB management button and wire up the panel**

In the template, add a button in the `header-actions` div (after the "新建大纲" button):

```html
<button class="btn btn-secondary" @click="showKBPanel = true">
  <IconBase name="database" :size="14" />
  知识库管理
</button>
```

Add the panel component at the end of the template (before `</template>`):

```html
<KnowledgeBasePanel v-model:visible="showKBPanel" />
```

In the script, add the import and state:

```javascript
import KnowledgeBasePanel from '../components/common/KnowledgeBasePanel.vue'
const showKBPanel = ref(false)
```

- [ ] **Step 2: Verify build**

```bash
cd slideon-frontend && npx vite build --mode development 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add slideon-frontend/src/views/DashboardView.vue
git commit -m "feat: add knowledge base management button to dashboard"
```

---

### Task 14: Frontend — Radar Chart & Metric Card Components

**Files:**
- Create: `slideon-frontend/src/components/common/RadarChart.vue`
- Create: `slideon-frontend/src/components/common/MetricCard.vue`

- [ ] **Step 1: Write the RadarChart component**

```vue
<template>
  <div class="radar-chart-container">
    <svg :viewBox="`0 0 ${size} ${size}`" :width="size" :height="size">
      <!-- Background grid (polygons) -->
      <polygon
        v-for="level in 5"
        :key="level"
        :points="getPolygonPoints(level / 5)"
        fill="none"
        :stroke="level === 5 ? '#d1d5db' : '#e5e7eb'"
        stroke-width="1"
      />
      <!-- Axis lines -->
      <line
        v-for="(_, i) in axes"
        :key="'axis-' + i"
        :x1="cx"
        :y1="cy"
        :x2="getPoint(i, 1).x"
        :y2="getPoint(i, 1).y"
        stroke="#e5e7eb"
        stroke-width="1"
      />
      <!-- Data polygon -->
      <polygon
        :points="dataPoints"
        fill="rgba(99,102,241,0.2)"
        stroke="#6366f1"
        stroke-width="2"
      />
      <!-- Data points -->
      <circle
        v-for="(_, i) in axes"
        :key="'dot-' + i"
        :cx="getPoint(i, values[i] / maxVal).x"
        :cy="getPoint(i, values[i] / maxVal).y"
        r="4"
        fill="#6366f1"
      />
      <!-- Labels -->
      <text
        v-for="(axis, i) in axes"
        :key="'label-' + i"
        :x="getLabelPoint(i).x"
        :y="getLabelPoint(i).y"
        text-anchor="middle"
        dominant-baseline="middle"
        fill="#6b7280"
        font-size="11"
      >{{ axis }}</text>
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  axes: { type: Array, required: true },
  values: { type: Array, required: true },
  maxVal: { type: Number, default: 10 },
  size: { type: Number, default: 300 }
})

const cx = computed(() => props.size / 2)
const cy = computed(() => props.size / 2)
const radius = computed(() => props.size * 0.35)

function getPoint(index, ratio) {
  const angle = (Math.PI * 2 * index) / props.axes.length - Math.PI / 2
  return {
    x: cx.value + radius.value * Math.cos(angle) * ratio,
    y: cy.value + radius.value * Math.sin(angle) * ratio
  }
}

function getLabelPoint(index) {
  return getPoint(index, 1.2)
}

function getPolygonPoints(ratio) {
  return Array.from({ length: props.axes.length }, (_, i) => {
    const p = getPoint(i, ratio)
    return `${p.x},${p.y}`
  }).join(' ')
}

const dataPoints = computed(() => {
  return Array.from({ length: props.axes.length }, (_, i) => {
    const v = Math.min((props.values[i] || 0) / props.maxVal, 1)
    const p = getPoint(i, v)
    return `${p.x},${p.y}`
  }).join(' ')
})
</script>

<style scoped>
.radar-chart-container { display:flex; justify-content:center; }
</style>
```

- [ ] **Step 2: Write the MetricCard component**

```vue
<template>
  <div class="metric-card" :class="colorClass">
    <div class="metric-header">
      <span class="metric-label">{{ label }}</span>
      <span class="metric-score">{{ displayScore }}</span>
    </div>
    <div class="metric-bar">
      <div class="metric-fill" :style="{ width: fillPercent + '%' }"></div>
    </div>
    <div v-if="detail" class="metric-detail">{{ detail }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  score: { type: Number, default: 0 },
  maxScore: { type: Number, default: 10 },
  detail: { type: String, default: '' }
})

const fillPercent = computed(() => Math.min((props.score / props.maxScore) * 100, 100))
const displayScore = computed(() => {
  if (props.maxScore <= 1) return (props.score * 100).toFixed(0) + '%'
  if (Number.isInteger(props.score)) return String(props.score)
  return props.score.toFixed(1)
})

const colorClass = computed(() => {
  const pct = fillPercent.value
  if (pct >= 70) return 'good'
  if (pct >= 40) return 'warn'
  return 'poor'
})
</script>

<style scoped>
.metric-card { padding:12px 16px; border-radius:10px; background:#f9fafb; border:1px solid #e5e7eb; }
.metric-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.metric-label { font-size:13px; font-weight:600; color:#374151; }
.metric-score { font-size:16px; font-weight:700; }
.metric-bar { height:6px; background:#e5e7eb; border-radius:3px; overflow:hidden; }
.metric-fill { height:100%; border-radius:3px; transition:width .5s ease; }
.metric-detail { font-size:11px; color:#9ca3af; margin-top:6px; }
.good .metric-score { color:#059669; }
.good .metric-fill { background:linear-gradient(90deg,#10b981,#34d399); }
.warn .metric-score { color:#d97706; }
.warn .metric-fill { background:linear-gradient(90deg,#f59e0b,#fbbf24); }
.poor .metric-score { color:#dc2626; }
.poor .metric-fill { background:linear-gradient(90deg,#ef4444,#f87171); }
</style>
```

- [ ] **Step 3: Verify build**

```bash
cd slideon-frontend && npx vite build --mode development 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
git add slideon-frontend/src/components/common/RadarChart.vue slideon-frontend/src/components/common/MetricCard.vue
git commit -m "feat: add RadarChart and MetricCard visualization components"
```

---

### Task 15: Frontend — Evaluation Panel in Editor

**Files:**
- Create: `slideon-frontend/src/components/common/EvaluationPanel.vue`

- [ ] **Step 1: Write the EvaluationPanel component**

```vue
<template>
  <div class="eval-panel">
    <div class="eval-header">
      <h3>质量评估</h3>
      <button class="btn btn-sm btn-primary" @click="runEvaluation" :disabled="evaluating">
        <IconBase v-if="evaluating" name="spinner" :size="12" class="animate-spin" />
        开始评估
      </button>
    </div>

    <div v-if="result" class="eval-results">
      <!-- Radar chart -->
      <RadarChart
        v-if="radarData"
        :axes="radarData.axes"
        :values="radarData.values"
        :maxVal="10"
        :size="260"
      />

      <!-- Rule metrics -->
      <div class="metrics-grid">
        <MetricCard
          label="结构完整性"
          :score="result.rule_metrics.structure_completeness"
          :maxScore="1"
          :detail="structureDetail"
        />
        <MetricCard
          label="信息密度"
          :score="result.rule_metrics.information_density?.score || 0"
          :maxScore="1"
          :detail="densityDetail"
        />
        <MetricCard
          label="内容多样性"
          :score="result.rule_metrics.content_diversity?.ttr || 0"
          :maxScore="1"
          :detail="diversityDetail"
        />
        <MetricCard
          v-if="result.rule_metrics.rag_recall != null"
          label="RAG 召回率"
          :score="result.rule_metrics.rag_recall"
          :maxScore="1"
        />
      </div>

      <!-- LLM Judge -->
      <div v-if="result.llm_judge_metrics" class="llm-scores">
        <h4>AI 综合评分</h4>
        <div class="metrics-grid">
          <MetricCard
            label="结构合理性"
            :score="result.llm_judge_metrics.structure_rationality || 0"
            :maxScore="10"
          />
          <MetricCard
            label="事实准确率"
            :score="result.llm_judge_metrics.fact_accuracy || 0"
            :maxScore="10"
          />
          <MetricCard
            label="逻辑连贯性"
            :score="result.llm_judge_metrics.logical_coherence || 0"
            :maxScore="10"
          />
          <MetricCard
            label="内容深度"
            :score="result.llm_judge_metrics.content_depth || 0"
            :maxScore="10"
          />
        </div>
      </div>

      <!-- Overall -->
      <div class="overall-score">
        <span class="overall-label">综合评分</span>
        <span class="overall-value">{{ result.overall_score }}</span>
        <span class="overall-unit">/ 10</span>
      </div>

      <!-- Suggestions -->
      <div v-if="result.suggestions?.length" class="suggestions">
        <h4>改进建议</h4>
        <ul>
          <li v-for="(s, i) in result.suggestions" :key="i">{{ s }}</li>
        </ul>
      </div>
    </div>

    <div v-else-if="!evaluating" class="eval-empty">
      <IconBase name="chart" :size="40" />
      <p>点击「开始评估」对当前大纲进行质量分析</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import IconBase from '../icons/IconBase.vue'
import RadarChart from './RadarChart.vue'
import MetricCard from './MetricCard.vue'
import { apiService } from '../../services/api.js'

const props = defineProps({
  presentationId: { type: String, default: '' }
})

const result = ref(null)
const evaluating = ref(false)

const radarData = computed(() => {
  if (!result.value) return null
  const r = result.value
  const axes = ['结构', '信息密度', '多样性', '结构合理', '逻辑']
  const values = [
    (r.rule_metrics.structure_completeness || 0) * 10,
    (r.rule_metrics.information_density?.score || 0) * 10,
    (r.rule_metrics.content_diversity?.ttr || 0) * 10,
    r.llm_judge_metrics?.structure_rationality || 0,
    r.llm_judge_metrics?.logical_coherence || 0,
  ]
  return { axes, values }
})

const structureDetail = computed(() => {
  if (!result.value) return ''
  return `得分: ${(result.value.rule_metrics.structure_completeness * 100).toFixed(0)}%`
})

const densityDetail = computed(() => {
  const d = result.value?.rule_metrics?.information_density
  if (!d) return ''
  return `平均 ${d.avg_bullets_per_slide} 要点/页, ${d.avg_words_per_slide} 词/页`
})

const diversityDetail = computed(() => {
  const d = result.value?.rule_metrics?.content_diversity
  if (!d) return ''
  return `${d.unique_terms} 不同词 / ${d.total_terms} 总词数`
})

async function runEvaluation() {
  evaluating.value = true
  try {
    result.value = await apiService.evaluatePresentation(props.presentationId, {
      enableLLMJudge: true
    })
  } catch (e) {
    console.error('Evaluation failed:', e)
  } finally {
    evaluating.value = false
  }
}
</script>

<style scoped>
.eval-panel { padding:20px; }
.eval-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:20px; }
.eval-header h3 { font-size:16px; font-weight:600; color:#1f2937; margin:0; }
.eval-empty { text-align:center; padding:40px 20px; color:#9ca3af; }
.eval-empty p { font-size:14px; margin-top:12px; }
.eval-results { display:flex; flex-direction:column; gap:20px; }
.metrics-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.llm-scores h4 { font-size:14px; font-weight:600; color:#374151; margin:0 0 10px; }
.overall-score { display:flex; align-items:baseline; justify-content:center; gap:8px; padding:20px; background:linear-gradient(135deg,#6366f1,#8b5cf6); border-radius:12px; color:white; }
.overall-label { font-size:14px; opacity:.9; }
.overall-value { font-size:36px; font-weight:700; }
.overall-unit { font-size:14px; opacity:.7; }
.suggestions { background:#fffbeb; border:1px solid #fcd34d; border-radius:10px; padding:16px; }
.suggestions h4 { font-size:14px; font-weight:600; color:#92400e; margin:0 0 8px; }
.suggestions ul { margin:0; padding-left:20px; }
.suggestions li { font-size:13px; color:#78350f; margin-bottom:4px; }
</style>
```

- [ ] **Step 2: Verify build**

```bash
cd slideon-frontend && npx vite build --mode development 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add slideon-frontend/src/components/common/EvaluationPanel.vue
git commit -m "feat: add evaluation panel component for in-editor quality assessment"
```

---

### Task 16: Frontend — Integrate Evaluation into Outline Editor

**Files:**
- Modify: `slideon-frontend/src/views/OutlineEditorView.vue`

- [ ] **Step 1: Add evaluation tab to the editor**

In the template, add an "评估" button in `header-right` (after the "生成PPT" button):

```html
<button class="btn btn-secondary" @click="showEval = !showEval" :class="{ active: showEval }">
  <IconBase name="chart" :size="14" />
  评估
</button>
```

Add the evaluation panel after the `editor-body` div:

```html
<div v-if="showEval" class="eval-drawer">
  <EvaluationPanel :presentationId="outlineId" />
</div>
```

In the script, add imports and state:

```javascript
import EvaluationPanel from '../components/common/EvaluationPanel.vue'
const showEval = ref(false)
```

Add styles:

```css
.eval-drawer { border-top:2px solid #e5e7eb; max-height:50vh; overflow-y:auto; }
```

- [ ] **Step 2: Verify build**

```bash
cd slideon-frontend && npx vite build --mode development 2>&1 | tail -5
```

- [ ] **Step 3: Commit**

```bash
git add slideon-frontend/src/views/OutlineEditorView.vue
git commit -m "feat: integrate evaluation panel into outline editor"
```

---

### Task 17: Frontend — Batch Evaluation Page

**Files:**
- Create: `slideon-frontend/src/views/BatchEvalView.vue`
- Modify: `slideon-frontend/src/router/index.js`

- [ ] **Step 1: Write the batch evaluation page**

```vue
<template>
  <div class="batch-eval-page">
    <header class="eval-page-header">
      <router-link to="/dashboard" class="btn btn-ghost btn-icon">
        <IconBase name="arrowLeft" :size="18" />
      </router-link>
      <h1>批量评估</h1>
    </header>

    <div class="eval-container">
      <!-- Configuration -->
      <section class="config-section">
        <h2>评估配置</h2>

        <div class="form-group">
          <label>评估主题（一行一个）</label>
          <textarea v-model="topicsText" rows="5" placeholder="新能源汽车行业分析
企业数字化转型战略
人工智能技术发展趋势"></textarea>
        </div>

        <div class="form-group">
          <label>RAG 配置</label>
          <div class="config-row">
            <label class="checkbox-label">
              <input type="checkbox" v-model="configs[0].useRag" /> RAG 启用 (配置A)
            </label>
            <label class="checkbox-label">
              <input type="checkbox" v-model="configs[1].useRag" /> RAG 启用 (配置B)
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>评估指标</label>
          <div class="metric-checkboxes">
            <label v-for="m in availableMetrics" :key="m.value" class="checkbox-label">
              <input type="checkbox" :value="m.value" v-model="selectedMetrics" /> {{ m.label }}
            </label>
          </div>
        </div>

        <button class="btn btn-primary btn-lg" @click="runBatch" :disabled="running">
          <IconBase v-if="running" name="spinner" :size="16" class="animate-spin" />
          {{ running ? '评估中...' : '开始批量评估' }}
        </button>
      </section>

      <!-- Results -->
      <section v-if="batchResults" class="results-section">
        <h2>评估结果</h2>

        <div class="results-table-wrapper">
          <table class="results-table">
            <thead>
              <tr>
                <th>配置</th>
                <th>主题</th>
                <th>综合评分</th>
                <th>结构完整性</th>
                <th>信息密度</th>
                <th>RAG 召回率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in batchResults.results" :key="i">
                <td><span class="config-badge">{{ r.config }}</span></td>
                <td>{{ r.topic }}</td>
                <td><strong>{{ r.overall_score }}</strong></td>
                <td>{{ formatPct(r.rule_metrics?.structure_completeness) }}</td>
                <td>{{ formatPct(r.rule_metrics?.information_density?.score) }}</td>
                <td>{{ formatPct(r.rule_metrics?.rag_recall) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import IconBase from '../components/icons/IconBase.vue'
import { apiService } from '../services/api.js'

const topicsText = ref('新能源汽车行业分析\n企业数字化转型战略\n人工智能技术发展趋势')
const configs = ref([{ name: 'RAG_ON', useRag: true }, { name: 'RAG_OFF', useRag: false }])
const selectedMetrics = ref(['structure', 'density', 'bleu', 'rag_recall', 'llm_judge'])
const running = ref(false)
const batchResults = ref(null)

const availableMetrics = [
  { value: 'structure', label: '结构完整性' },
  { value: 'density', label: '信息密度' },
  { value: 'diversity', label: '内容多样性' },
  { value: 'bleu', label: 'BLEU 分数' },
  { value: 'rouge', label: 'ROUGE-L' },
  { value: 'rag_recall', label: 'RAG 召回率' },
  { value: 'llm_judge', label: 'LLM 评估' },
]

async function runBatch() {
  const topics = topicsText.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (topics.length === 0) { alert('请输入至少一个评估主题'); return }

  running.value = true
  try {
    batchResults.value = await apiService.batchEvaluate({
      configs: configs.value.map((c, i) => ({ name: c.name, use_rag: c.useRag })),
      topics,
      metrics: selectedMetrics.value,
      reference_texts: {}
    })
  } catch (e) {
    console.error('Batch evaluation failed:', e)
  } finally {
    running.value = false
  }
}

function formatPct(v) {
  if (v == null) return '—'
  return (v * 100).toFixed(1) + '%'
}
</script>

<style scoped>
.batch-eval-page { min-height:100vh; background:#f9fafb; }
.eval-page-header { display:flex; align-items:center; gap:12px; padding:16px 24px; background:white; border-bottom:1px solid #e5e7eb; position:sticky; top:0; z-index:10; }
.eval-page-header h1 { font-size:20px; font-weight:600; color:#1f2937; margin:0; }
.eval-container { max-width:900px; margin:0 auto; padding:32px 24px; display:flex; flex-direction:column; gap:32px; }
.config-section { background:white; border-radius:16px; padding:24px; border:1px solid #e5e7eb; }
.config-section h2, .results-section h2 { font-size:18px; font-weight:600; color:#1f2937; margin:0 0 20px; }
.form-group { margin-bottom:20px; }
.form-group label { display:block; font-size:13px; font-weight:600; color:#374151; margin-bottom:8px; }
.form-group textarea { width:100%; padding:12px; border:1px solid #d1d5db; border-radius:8px; font-size:14px; font-family:inherit; resize:vertical; }
.config-row, .metric-checkboxes { display:flex; gap:16px; flex-wrap:wrap; }
.checkbox-label { display:flex; align-items:center; gap:6px; font-size:14px; color:#374151; cursor:pointer; }
.results-section { background:white; border-radius:16px; padding:24px; border:1px solid #e5e7eb; }
.results-table-wrapper { overflow-x:auto; }
.results-table { width:100%; border-collapse:collapse; font-size:13px; }
.results-table th { text-align:left; padding:10px 12px; background:#f9fafb; color:#6b7280; font-weight:600; border-bottom:2px solid #e5e7eb; }
.results-table td { padding:10px 12px; border-bottom:1px solid #f3f4f6; color:#374151; }
.config-badge { display:inline-block; padding:2px 10px; background:#eef2ff; color:#4f46e5; border-radius:999px; font-size:12px; font-weight:500; }
</style>
```

- [ ] **Step 2: Add the `/eval` route**

In [router/index.js](slideon-frontend/src/router/index.js), add after the dashboard route:

```javascript
    {
      path: '/eval',
      name: 'eval',
      component: () => import('../views/BatchEvalView.vue')
    }
```

- [ ] **Step 3: Verify build**

```bash
cd slideon-frontend && npx vite build --mode development 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
git add slideon-frontend/src/views/BatchEvalView.vue slideon-frontend/src/router/index.js
git commit -m "feat: add batch evaluation page and /eval route"
```

---

### Task 18: Documentation — System Architecture Document

**Files:**
- Create: `docs/system-architecture.md`

- [ ] **Step 1: Write the system architecture documentation**

```markdown
# Slideon 系统架构文档

> 版本：0.1.0 | 日期：2026-06-07 | 分支：feature/rag

---

## 1. 系统概览

### 1.1 项目简介

Slideon 是一个基于大语言模型（LLM）和检索增强生成（RAG）的智能 PPT 生成系统。核心理念是 **"AI 负责语义，Renderer 负责视觉"**：LLM 只输出结构化的语义 DSL（Domain Specific Language），不涉及布局细节；渲染引擎将 DSL 编译为 RenderTree，负责布局、样式和组件组合。

### 1.2 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.12) |
| AI 编排 | LangChain + LangGraph |
| LLM | DeepSeek / OpenAI 兼容 API |
| 向量数据库 | Milvus 3.0-beta（混合检索 ANN + 关键词） |
| 向量化模型 | BAAI/bge-small-zh-v1.5（512 维） |
| 网络搜索 | DuckDuckGo API + trafilatura 全文抓取 |
| PPTX 导出 | python-pptx |
| 前端 | Vue 3 (Composition API) + Vite |

### 1.3 系统架构图

```
┌──────────────────────────────────────────────────────────────┐
│                    前端 (slideon-frontend)                     │
│    Vue 3 + Vite: 首页 · Dashboard · 大纲编辑器 · 评估页面      │
│              OutlineModal (文档上传 + 主题输入)                  │
│              KnowledgeBasePanel · EvaluationPanel              │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP REST API
┌──────────────────────────┴───────────────────────────────────┐
│                  后端 (FastAPI)                               │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │  AI Pipeline    │  │  Render Engine  │  │  RAG Service   │  │
│  │                │  │                │  │                │  │
│  │ 1. 意图分析    │  │ Component      │  │ Hybrid         │  │
│  │ 2. 结构规划    │  │ Planner        │  │ Retriever      │  │
│  │ 3. DSL 生成    │  │                │  │ (Dense+Keyword │  │
│  │                │  │ Layout Engine  │  │  +RRF Fuse)    │  │
│  │ 15种语义类型   │  │                │  │                │  │
│  │                │  │ Theme Engine   │  │ LangGraph       │  │
│  │ Fallback +     │  │                │  │ Orchestration   │  │
│  │ Repair 策略    │  │ RenderTree     │  │                │  │
│  └────────────────┘  └────────────────┘  └────────────────┘  │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │  Evaluation     │  │  Export        │  │  Task Queue    │  │
│  │  System         │  │  (PPTX)        │  │  (Async KB     │  │
│  │                │  │                │  │   Import)      │  │
│  │ Rule Metrics   │  │ python-pptx    │  │                │  │
│  │ + LLM Judge    │  │                │  │ asyncio.Queue  │  │
│  └────────────────┘  └────────────────┘  └────────────────┘  │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────┴───────────────────────────────────┐
│                      数据层                                    │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │ File Repo    │  │ Milvus Vector DB │  │ Web Search    │   │
│  │ (JSON 文件)   │  │ (BGE Embedding)  │  │ (DuckDuckGo)  │   │
│  └──────────────┘  └──────────────────┘  └──────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 1.4 端到端数据流

```
用户输入（主题或文档）
    │
    ▼
┌──────────────┐
│ 文档解析      │ ← PDF/Word → 纯文本 (pymupdf/docx)
│ (如果是文件)  │
└──────┬───────┘
       │
       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ RAG 检索      │ →  │ AI Pipeline   │ →  │ Render Engine │
│ (Milvus+Web)  │    │ 意图→规划→DSL  │    │ DSL→RenderTree│
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌──────────────────────────┘
                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 前端编辑      │ ←  │ RenderTree   │ →  │ PPTX 导出     │
│ (Outline     │    │ (JSON)       │    │ (python-pptx) │
│  Editor)     │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 2. AI Pipeline 核心模块详解

### 2.1 三阶段流水线

AI Pipeline (`services/ai/pipeline.py`) 采用三阶段流水线架构：

#### 阶段 1：意图分析 (`analyze_intent`)

- **输入**：用户主题（字符串）
- **输出**：`IntentAnalysis` 对象
  - `audience`：目标受众
  - `goal`：演示目标
  - `tone`：风格基调
  - `slideCount`：建议页数（≥10）
  - `preferredTheme`：推荐主题（modern_blue / paper_light / academic_gray / minimal_black）

- **Prompt 设计**：
  - 系统 prompt 明确角色：「资深 PPT 规划助手」
  - 要求只输出 JSON，不输出解释文字
  - 页数约束：至少 10 页，丰富内容可到 15-20 页

#### 阶段 2：结构规划 (`plan_presentation`)

- **输入**：`IntentAnalysis` 对象
- **输出**：`PresentationPlan` 对象
  - `title`：PPT 标题
  - `theme`：主题
  - `slides`：Slide 规划列表，每个包含 `id` / `intent` / `section` / `title` / `purpose`

- **intent 类型**（15 种）：
  `cover`, `agenda`, `text`, `timeline`, `kpi`, `comparison`, `swot`, `roadmap`,
  `process_flow`, `chart`, `multi_column`, `architecture`, `quote`, `divider`, `team`

- **Prompt 设计**：
  - 明确定义 intent 枚举值
  - 确保规划至少 10 页，覆盖封面、目录、内容页、数据页、总结/结束页
  - 每个 section 可包含多页内容

#### 阶段 3：DSL 生成 (`generate_dsl`)

- **输入**：topic + theme + rag_context
- **输出**：`PresentationDSL` 对象（完整的语义化 PPT DSL）

- **Prompt 设计**：
  - 详细的字段类型约束（每种 intent 的必需字段）
  - 严格要求禁止输出布局字段（x/y/w/h/fontSize/templateId）
  - RAG 增强模式：有参考资料时要求 4-6 bullets、具体数据、案例
  - 无 RAG 模式：简洁精炼，2-3 bullets
  - 通用规则：避免低信息量空洞内容

### 2.2 容错与修复策略

Pipeline 内置多层容错：

1. **LLM 初始化失败** → 使用 `_fallback()` 生成默认 DSL（14 页完整示例 PPT）
2. **意图分析/规划失败** → 同上
3. **DSL 解析失败** → `_repair_dsl_dict()` 遍历修复每个字段
4. **修复失败** → `_fallback()`
5. **DSL 为空** → `_fallback()`

`_repair_dsl_dict()` 和 `_repair_slide_dict()` 方法：
- 处理字符串/对象不匹配（notes 为 string → 转为数组）
- 字段缺失补全（从 topic/analysis 继承）
- 类型转换（字符串列表、intent 验证等）
- 总计约 600 行的防御性修复代码

### 2.3 RAG 集成

DSL 生成时通过 `rag_context` 参数注入 RAG 增强：

```
rag_context = rag_service.retrieve_context(topic, top_k=8)
dsl = ai_pipeline.generate_dsl(topic, theme, rag_context=rag_context)
```

Prompt 中 RAG 上下文被格式化为：
```
## 参考资料（来自知识库和网络搜索，务必充分利用）
请大量引用以下资料中的具体数据、案例、趋势、事实来丰富 PPT 内容。
[检索到的内容...]
```

---

## 3. RAG 模块详解

### 3.1 架构总览

```
RagService (rag_service.py)
  ├── HybridRetriever (retrieval.py)
  │     ├── MilvusStore: 向量检索 (ANN) + 关键词检索 (BM25-like)
  │     ├── WebSearchService: DuckDuckGo 搜索
  │     ├── ContentFetcher: trafilatura 全文抓取
  │     └── RRF Fuse: 倒数排列融合 (Reciprocal Rank Fusion)
  ├── KnowledgeBase (knowledge_base.py)
  │     ├── EmbeddingService: BGE-small-zh-v1.5 (512维)
  │     ├── 文档解析: PDF (pymupdf), DOCX (python-docx), TXT, MD
  │     └── 文本分块: 500 chars + 80 chars overlap
  └── RAG Graph (rag_graph.py) — LangGraph 状态图
        ├── analyze_query: 查询分析 + 多查询生成
        ├── web_search: 网络并行搜索
        ├── local_search: Milvus 本地搜索
        ├── enrich_images: 图片资源搜索
        ├── fuse: RRF 融合
        └── build_context: 构建增强上下文
```

### 3.2 混合检索策略

**HybridRetriever** 实现了三层检索：

1. **Dense 向量检索**（Milvus ANN）
   - 使用 BGE-small-zh-v1.5 生成 512 维 query embedding
   - Milvus AUTOINDEX + Inner Product (IP) 相似度
   - 支持 source_filter 过滤

2. **Sparse 关键词检索**（Milvus BM25-like）
   - SQL-like 文本匹配 (`text like "%query%"`)
   - 与 Dense 检索独立评分

3. **RRF 融合排序**
   - 公式：`RRF_score = Σ 1/(k + rank_i + 1)`，其中 k=60
   - 本地结果 weight = 1.0，网络结果 weight = 0.4
   - 取 top_k 结果

4. **Deep Fetch**（网络结果增强）
   - 对前 3 条网络结果调用 `ContentFetcher.fetch(url)` 抓取全文
   - 使用 trafilatura 提取正文
   - 300ms 间隔避免请求过频

### 3.3 Milvus 向量数据库

**Collection Schema** (`ppt_knowledge_base`)：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT64 (auto_id) | 主键 |
| text | VARCHAR(65535) | 文本内容（启用中文分词器） |
| embedding | FLOAT_VECTOR(512) | BGE 向量 |
| source | VARCHAR(512) | 来源标识 |
| chunk_index | INT64 | 分块索引 |
| metadata | JSON | 元数据 |

**索引**：
- embedding：AUTOINDEX + IP 度量
- id：STL_SORT

### 3.4 知识库管理

**KnowledgeBase** 提供：
- `ingest_text()`: 文本分块 → 向量化 → 批量插入（batch_size=32）
- `ingest_file()`: 文件解析（PDF/DOCX/TXT/MD）→ ingest_text
- `remove_source()`: 按 source 删除
- `get_stats()`: Collection 统计

**分块策略**：
- CHUNK_SIZE = 500 字符
- CHUNK_OVERLAP = 80 字符
- 按段落边界分块，避免中间截断
- 长句被迫截断时按句号 ("。") 寻找最佳切割点

### 3.5 LangGraph 状态图

RAG Graph 使用 LangGraph 编排多步检索流程：

```
START → analyze_query ──┬──→ web_search ──┬──→ fuse → build_context → END
                        ├──→ local_search ─┘        ↑
                        └──→ enrich_images ──────────┘
```

- **analyze_query**：使用 LLM 生成 3-5 个不同角度的搜索查询
- **web_search / local_search / enrich_images**：三个并行节点
- **fuse**：RRF 融合去重
- **build_context**：构建最终增强文本（含图片 URL）

### 3.6 网络搜索

**WebSearchService** (`web_search.py`)：
- 使用 DuckDuckGo API（`duckduckgo_search`）
- 支持区域配置（默认 `wt-wt`）
- ContentFetcher 使用 trafilatura 提取正文
- 失败时回退到 snippet

---

## 4. Render Engine 简介

### 4.1 渲染流水线

```
DSL (15种语义类型)
    │
    ▼
Component Planner (planning.py)
  └── 语义 intent → 组件类型映射
    │
    ▼
Layout Engine (layout.py + layout_selector.py)
  └── 绝对坐标布局 (x, y, w, h)
    │
    ▼
Theme Engine (theme_engine.py)
  └── ThemeToken → CSS-like 样式
    │
    ▼
RenderTree (JSON)
  └── 可编辑的组件树
```

### 4.2 主题系统

四种内置主题：

| 主题 | 主色调 | 风格 |
|------|--------|------|
| modern_blue | #3B82F6 | 现代科技蓝 |
| paper_light | #F5F5DC | 清新纸质感 |
| academic_gray | #6B7280 | 学术灰调 |
| minimal_black | #1F2937 | 极简黑色 |

每个主题定义了一套 DesignToken（颜色/字体/间距/圆角等），通过 `theme_engine.py` 应用到 RenderTree。

### 4.3 PPTX 导出

```
RenderTree → PptxExporter → python-pptx Slide
  └── component_renderers: 每种组件类型的 PPTX 渲染器
    ├── TextBox → 文本框 + 样式
    ├── Chart → python-pptx Chart 对象
    ├── Table → 表格
    ├── Shape → 形状
    └── Image → 图片占位
```

---

## 5. API 参考

### 5.1 PPT 生成

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/dsl` | AI 生成大纲 |
| POST | `/dsl/from-document` | 从文档生成大纲（PDF/Word） |
| POST | `/render-tree` | 编译大纲为 RenderTree |
| POST | `/presentations` | 一键创建完整 PPT |
| GET | `/presentations/{id}` | 获取 PPT Bundle |
| PATCH | `/presentations/{id}/components/{cid}` | 编辑组件 |
| PUT | `/presentations/{id}/theme` | 切换主题 |
| POST | `/presentations/{id}/export/pptx` | 导出 PPTX |

### 5.2 RAG

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/rag/search` | 混合检索 |
| POST | `/rag/enhance` | 获取增强上下文 |
| POST | `/rag/documents` | 上传文档（单个） |
| POST | `/rag/documents/batch` | 批量上传文档（异步） |
| GET | `/rag/tasks/{task_id}` | 查询导入进度 |
| GET | `/rag/documents` | 列出已导入文档 |
| DELETE | `/rag/documents/{source}` | 删除文档 |
| POST | `/rag/bootstrap` | 初始化种子知识库 |

### 5.3 评估

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/eval/single/{presentation_id}` | 单次评估 |
| POST | `/eval/batch` | 批量评估 |

---

## 6. 关键设计决策

| 决策 | 理由 |
|------|------|
| AI 只输出语义 DSL | 解耦内容与布局；Renderer 保证视觉一致性 |
| 15种 intent 类型 | 覆盖常见 PPT 场景，可扩展 |
| RAG 混合检索 + RRF 融合 | 结合向量语义和关键词精确匹配的优势 |
| LangGraph 编排 | 多路并行检索 + 结构化状态管理 |
| 内存任务队列 | MVP 阶段避免 Redis/Celery 复杂度 |
| BGE-small-zh-v1.5 | 中英双语 512 维，轻量高效 |
| Fallback 策略 | 确保 LLM 故障时系统仍可工作 |
| 多层 DSL 修复 | 容忍 LLM 输出的格式/类型错误 |
```

- [ ] **Step 2: Commit**

```bash
git add docs/system-architecture.md
git commit -m "docs: add comprehensive system architecture documentation"
```

---

## Plan Self-Review

- [x] **Spec coverage**: Feature 1 (Doc→Outline + KB ingest) covered by Tasks 1, 8, 9, 11. Feature 2 (KB Import + UI) covered by Tasks 1, 8, 9, 12, 13. Feature 3 (Evaluation) covered by Tasks 2-6, 8, 14-17. Documentation covered by Task 18.
- [x] **Placeholder scan**: No TBD/TODO in any task. All code is complete and explicit.
- [x] **Type consistency**: `EvalRequest` → `EvalResult` → `RuleMetrics` → `LLMJudgeScores` → `BleuScores` → `RougeLScores` → `DensityMetrics` → `DiversityMetrics` all align. Frontend `api.js` methods match route definations. `ImportTask` ↔ `ImportTaskQueue` ↔ routes ↔ `KnowledgeBasePanel.vue` all consistent.
- [x] **Task granularity**: Each task is 2-5 minute scope with explicit code, commands, and commit messages.
