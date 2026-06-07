# Design Spec: Long Document Parsing, Knowledge Base Import & Evaluation System

**Date**: 2026-06-07
**Branch**: `feature/rag`
**Status**: Design Approved → Implementation Pending

---

## Overview

This specification covers three interconnected features for the Slideon AI PPT generation system:

1. **Long Document Parsing** — Upload documents (PDF, Word, TXT, MD) to generate outlines directly, with automatic knowledge base ingestion
2. **Knowledge Base Import** — Independent async batch document import into Milvus with progress tracking
3. **End-to-End Evaluation System** — Quality assessment of PPT outlines and content using rule-based metrics + LLM-as-Judge, with both user self-evaluation and developer batch evaluation modes

---

## Feature 1: Long Document Parsing → Outline Generation

### User Story

> As a user, I want to upload a long document (e.g., a 50-page industry report) in the outline creation modal, and have Slideon parse it, generate a structured outline, and save the document to the knowledge base — all in one action.

### Flow

```
User clicks "导入文档" in floating ball modal
         │
         ▼
Selects file (PDF/DOCX/TXT/MD)
         │
         ▼
POST /dsl/from-document  ─────────────────────────────
         │                                              │
         ▼                                              ▼
Backend parses document text              Background: chunk → embed
         │                                      → Milvus insert
         ▼
Text injected as rag_context
into AI Pipeline (analyze_intent
→ plan_presentation → generate_dsl)
         │
         ▼
Returns outline JSON to frontend
```

### Backend Changes

#### New Endpoint: `POST /dsl/from-document`

- Accepts `multipart/form-data` with file field
- Parsing logic reuses `KnowledgeBase._read_file()` for PDF/DOCX/TXT/MD
- Calls `AiPipeline.generate_dsl()` with document text as rag_context
- Triggers async KB ingestion (fire-and-forget, does not block response)
- Returns standard outline JSON (same format as `POST /dsl`)

#### Implementation Notes

- Parse document in thread pool to avoid blocking the async event loop
- If document is very large (>10k chars), summarize/truncate intelligently before feeding to LLM prompt
- KB ingestion errors must NOT affect outline generation response
- File temporarily saved, parsed, then cleaned up

### Frontend Changes

#### OutlineModal.vue Modifications

- Add file upload area within the modal (click or drag-and-drop)
- Tab/toggle: "输入主题" | "导入文档"
- When document mode: show file picker + filename display
- File sent as FormData to `/dsl/from-document`
- Loading state: "正在解析文档并生成大纲..." (with cancel support)
- On success: navigate to outline editor as usual

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Document always ingested to KB | Maximizes knowledge reuse; users can later search against it |
| KB ingestion is fire-and-forget | Avoids delaying outline generation; KB insert failures don't block user |
| Document mode co-exists with text mode | Users can still type topics normally |

---

## Feature 2: Knowledge Base Import

### User Story

> As a user, I want to import documents into the knowledge base independently from outline generation, with support for batch upload and non-blocking progress tracking.

### Flow

```
Dashboard: User clicks "知识库管理" button
         │
         ▼
KB Management Panel opens
  ├── Upload area (batch drag-and-drop)
  │     └── POST /rag/documents (batch) → returns task_id
  │           └── Background processing: parse → chunk → embed → insert
  │                 └── Polling GET /rag/tasks/{task_id} for progress
  ├── Document list
  │     └── GET /rag/documents → list all ingested docs
  └── Delete action per document
        └── DELETE /rag/documents/{source}
```

### Backend Changes

#### New/Modified Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/rag/documents` | Extended: accept multiple files, return `task_id` |
| `GET` | `/rag/tasks/{task_id}` | Query import task progress (status, processed/total, errors) |
| `GET` | `/rag/documents` | **New**: List ingested documents with metadata |
| `DELETE` | `/rag/documents/{source}` | Existing: Remove document from KB |

#### Async Task Queue

- Simple in-memory `asyncio.Queue` + background worker (started at app startup)
- Task states: `pending` → `processing` → `completed` / `failed`
- Task result stored in memory dict keyed by `task_id` (survives for session lifetime)
- No external dependencies (no Celery/Redis needed for MVP)

```python
# New file: services/rag/task_queue.py
@dataclass
class ImportTask:
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    total: int
    processed: int
    errors: list[str]
    created_at: datetime
```

### Frontend Changes

#### New Component: `KnowledgeBasePanel.vue`

- Modal/panel triggered from Dashboard header
- Upload zone: drag-and-drop area, accepts PDF/DOCX/TXT/MD
- Progress display: per-file progress bars (non-blocking)
- Document list table: filename, chunks, import date, delete action
- Empty state: "还没有导入任何文档"

#### DashboardView.vue Modifications

- Add "知识库管理" button in header actions area
- Click opens `KnowledgeBasePanel` as a modal

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Async processing | Large documents can take minutes; must not block UI |
| In-memory task queue | Simplicity; no need for Redis/Celery at current scale |
| Polling over SSE/WebSocket | Simpler to implement; sufficient for progress updates |

---

## Feature 3: End-to-End Evaluation System

### Overview

Two evaluation modes:
- **User Self-Evaluation**: Integrated in the editor, helps users assess and improve their PPT
- **Developer Batch Evaluation**: Standalone page for systematic comparison across configurations

### Evaluation Metrics

#### Rule-Based / Statistical Metrics (Code, Deterministic)

| Metric | Calculation | Score Range |
|--------|-------------|-------------|
| Structure Completeness | Has cover + agenda + content + conclusion sections; intent type coverage | 0-1 |
| Information Density | Avg bullets per slide, avg words per slide, avg paragraphs per slide | 0-1 |
| Content Diversity | Type-Token Ratio (TTR) = unique terms / total terms | 0-1 |
| BLEU Score | n-gram precision against reference text (BLEU-1 through BLEU-4) | 0-1 |
| ROUGE-L | Longest common subsequence against reference | 0-1 |
| RAG Recall | Number of retrieved chunks cited/used / total retrieved chunks | 0-1 |
| RAG Precision | Number of relevant retrieved chunks / total retrieved chunks | 0-1 |

#### LLM-as-Judge Metrics (Semantic, 1-10 Scale)

| Metric | Prompt Focus |
|--------|-------------|
| Structure Rationality | Are sections logically ordered? Are transitions natural? |
| Fact Accuracy | Do claims match reference materials? Are there hallucinations? |
| Logical Coherence | Is there a clear narrative thread across slides? |
| Content Depth | Does content have specific data, cases, analysis — not just overviews? |
| Overall Quality | Holistic judgment of the PPT as a communication tool |

### Backend Architecture

```
services/evaluation/
├── __init__.py
├── schemas.py          # Pydantic models: EvalRequest, EvalResult, EvalReport
├── metrics.py          # Rule-based metrics: BLEU, ROUGE-L, structure, density, TTR
├── llm_judge.py        # LLM-as-Judge scoring with structured output
├── evaluator.py        # Orchestrator: runs all metrics, compiles report
└── rag_eval.py         # RAG-specific metrics: recall, precision
```

#### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/eval/single/{presentation_id}` | Evaluate a single PPT; returns full metrics report |
| `POST` | `/eval/batch` | Batch evaluation: specify topics + configs, returns comparison |
| `GET` | `/eval/report/{eval_id}` | Get a previously generated evaluation report |

#### `POST /eval/single/{presentation_id}` Request
```json
{
  "reference_text": "optional reference text for BLEU/ROUGE",
  "enable_llm_judge": true,
  "metrics": ["structure", "density", "diversity", "bleu", "rouge", "rag_recall", "llm_judge"]
}
```

#### Response Structure
```json
{
  "eval_id": "eval_xxx",
  "presentation_id": "pres_xxx",
  "rule_metrics": {
    "structure_completeness": 0.85,
    "information_density": {"avg_bullets_per_slide": 4.2, "avg_words_per_slide": 120, "score": 0.72},
    "content_diversity": {"ttr": 0.68, "unique_terms": 234, "total_terms": 344},
    "bleu": {"bleu-1": 0.45, "bleu-2": 0.32, "bleu-3": 0.21, "bleu-4": 0.15},
    "rouge_l": {"precision": 0.38, "recall": 0.42, "f1": 0.40},
    "rag_recall": 0.65,
    "rag_precision": 0.58
  },
  "llm_judge_metrics": {
    "structure_rationality": 8,
    "fact_accuracy": 7,
    "logical_coherence": 8,
    "content_depth": 6,
    "overall_quality": 7
  },
  "suggestions": ["建议增加数据可视化页", "KPI页可以补充具体数值", "总结页缺少明确的行动建议"],
  "overall_score": 7.2
}
```

#### `POST /eval/batch` — Batch Evaluation
```json
{
  "configs": [
    {"name": "RAG_ON_DeepSeek", "use_rag": true, "model": "DeepSeek-R1"},
    {"name": "RAG_OFF_DeepSeek", "use_rag": false, "model": "DeepSeek-R1"}
  ],
  "topics": ["新能源汽车行业分析", "企业数字化转型战略", "人工智能技术发展趋势"],
  "metrics": ["structure", "density", "bleu", "rag_recall", "llm_judge"],
  "reference_texts": {
    "新能源汽车行业分析": "reference text here...",
    "企业数字化转型战略": "reference text here..."
  }
}
```

### Frontend Changes

#### Evaluation in Editor (User Self-Evaluation)

- New "评估" tab/button in the OutlineEditor or Editor view
- On click: calls `POST /eval/single/{id}`
- Displays:
  - **Radar chart**: 6-axis (结构、信息密度、事实准确、逻辑连贯、内容深度、RAG效果)
  - **Metric cards**: each metric with score, color-coded (green/yellow/red)
  - **Suggestions list**: actionable improvement tips from LLM
  - **RAG metrics panel** (if RAG was used): recall/precision breakdown

#### Batch Evaluation Page (Developer Mode)

- New route: `/eval`
- Configuration panel:
  - Multi-select topics
  - Toggle RAG on/off per config
  - Select metrics to compute
  - Optional reference text input per topic
- Results: comparison table (configs as columns, metrics as rows) + bar charts

#### New Components
- `EvaluationPanel.vue` — embedded in editor
- `BatchEvalView.vue` — standalone page
- `RadarChart.vue` — radar/spider chart for metrics visualization
- `MetricCard.vue` — individual metric display

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Separate rule vs LLM metrics | Rule metrics are free and deterministic; LLM metrics cost API calls |
| BLEU/ROUGE require reference | Only computed when reference text is provided (optional) |
| RAG recall computed from retrieval logs | Need to track which chunks influenced the final content |
| Batch evaluation uses same pipeline | Ensures consistency; just varies config parameters |
| Suggestions are actionable | LLM prompt specifically asks for concrete, implementable improvements |

---

## Documentation Deliverable

In addition to the three features above, produce a technical documentation file:

**`docs/system-architecture.md`** — Comprehensive system architecture documentation covering:

1. **System Overview** — Architecture diagram, technology stack, data flow
2. **AI Pipeline Deep Dive** — Three-stage pipeline (Intent Analysis → Structure Planning → DSL Generation), prompt design, fallback strategy, repair logic
3. **RAG Module Deep Dive** — Milvus vector DB, BGE embeddings, hybrid retrieval (dense + keyword + RRF fusion), LangGraph orchestration, web search + deep fetch, knowledge base management
4. **Render Engine** — DSL → RenderTree compilation, component planner, layout engine, theme engine
5. **API Design** — Full endpoint reference with request/response examples

---

## Implementation Order

1. **Document Parsing + Outline Generation** (Feature 1) — foundational, touches AI Pipeline + RAG
2. **Knowledge Base Import UI** (Feature 2) — extends Feature 1's infrastructure
3. **Evaluation System** (Feature 3) — most complex, built on top of existing generation
4. **System Documentation** — written alongside implementation, finalized last

---

## File Change Summary

### Backend: New Files
- `backend/ppt_backend/services/rag/task_queue.py` — Async import task queue
- `backend/ppt_backend/services/evaluation/__init__.py`
- `backend/ppt_backend/services/evaluation/schemas.py`
- `backend/ppt_backend/services/evaluation/metrics.py`
- `backend/ppt_backend/services/evaluation/llm_judge.py`
- `backend/ppt_backend/services/evaluation/evaluator.py`
- `backend/ppt_backend/services/evaluation/rag_eval.py`

### Backend: Modified Files
- `backend/ppt_backend/api/routes.py` — New endpoints for doc parsing, KB, evaluation
- `backend/ppt_backend/api/main.py` — Start background task worker
- `backend/ppt_backend/container.py` — Wire new evaluation service
- `backend/ppt_backend/services/presentation_service.py` — Add evaluation methods
- `backend/ppt_backend/services/rag/retrieval.py` — Add retrieval logging for RAG eval

### Frontend: New Files
- `slideon-frontend/src/components/common/KnowledgeBasePanel.vue`
- `slideon-frontend/src/components/common/EvaluationPanel.vue`
- `slideon-frontend/src/components/common/RadarChart.vue`
- `slideon-frontend/src/components/common/MetricCard.vue`
- `slideon-frontend/src/views/BatchEvalView.vue`

### Frontend: Modified Files
- `slideon-frontend/src/components/common/OutlineModal.vue` — Add document upload
- `slideon-frontend/src/views/DashboardView.vue` — Add KB management button
- `slideon-frontend/src/views/OutlineEditorView.vue` — Integrate evaluation panel
- `slideon-frontend/src/services/api.js` — Add new API methods
- `slideon-frontend/src/config/api.js` — Add new endpoint config
- `slideon-frontend/src/router/index.js` — Add `/eval` route

### Documentation
- `docs/system-architecture.md` — New comprehensive architecture document

---

## Known Limitations & Future Work

| Limitation | Mitigation | Future |
|-----------|------------|--------|
| In-memory task queue — tasks lost on server restart | Acceptable for MVP; KB can be re-imported | Migrate to Redis/Celery if needed |
| Document text >10k chars may exceed LLM context window | Truncate intelligently (keep intro + conclusion + sampled sections) | Use Map-Reduce summarization for very long docs |
| BLEU/ROUGE require reference text | Metrics are optional; skipped when no reference provided | Auto-extract reference from KB for common topics |
| RAG recall depends on retrieval logging | Add lightweight logging to HybridRetriever | Store retrieval traces per generation for audit |
| Batch evaluation can be expensive (LLM calls × topics × configs) | Rate limiting; configurable metric selection | Add caching for repeated evaluations |
| PDF parsing requires `pymupdf` (fitz) | Already in requirements; graceful fallback | Add OCR support for scanned PDFs |

---

## Spec Self-Review Checklist

- [x] **Placeholder scan** — No TBD/TODO/ incomplete sections
- [x] **Internal consistency** — Features are interconnected (Doc parsing → KB → Eval); no contradictions
- [x] **Scope check** — 3 features + 1 doc; focused and deliverable in one plan
- [x] **Ambiguity check** — All metrics defined with score ranges; API contracts specified; fallback behaviors described
