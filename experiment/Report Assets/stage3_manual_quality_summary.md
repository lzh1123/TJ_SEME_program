# Stage 3 Manual Quality Evaluation Summary

## Scope

This stage evaluates representative generated outlines through manual review.
The goal is to complement automated latency and stability metrics with quality
judgment on outline structure and domain reliability.

## Sample Selection

Manual scoring uses 12 professional-topic outputs:

- 3 domains: software engineering, Alzheimer's disease, football
- 2 models: DeepSeek, Qwen
- 2 routes: pure LLM, RAG-enhanced
- 1 representative run per condition: `r1`

The selected samples are listed in:

- `Knowledge base/Report Assets/manual_quality_scores.csv`

## Scoring Rubric

Each sample was scored from 1 to 5 on:

- structure rationality
- logical coherence
- page granularity
- information density
- factual accuracy
- domain terminology
- presentation readiness

The full rubric is stored in:

- `Knowledge base/Report Assets/manual_quality_rubric.md`

## Model and Route Quality Summary

| Model | Route | Samples | Overall score | Factual accuracy | Domain terminology | Presentation readiness |
|---|---:|---:|---:|---:|---:|---:|
| DeepSeek | Pure LLM | 3 | 4.097 | 4.067 | 4.167 | 4.167 |
| DeepSeek | RAG-enhanced | 3 | 4.227 | 4.167 | 4.300 | 4.300 |
| Qwen | Pure LLM | 3 | 4.230 | 3.600 | 4.233 | 4.433 |
| Qwen | RAG-enhanced | 3 | 4.307 | 3.667 | 4.400 | 4.467 |

## Route-Level Quality Summary

| Route | Samples | Overall score | Structure | Logic | Information density |
|---|---:|---:|---:|---:|---:|
| Pure LLM | 6 | 4.163 | 4.300 | 4.300 | 4.217 |
| RAG-enhanced | 6 | 4.267 | 4.400 | 4.400 | 4.433 |

## Main Findings

### 1. RAG improves outline quality, but the gain is moderate

RAG-enhanced outputs show small improvements in:

- structure rationality
- logical coherence
- information density
- domain terminology
- presentation readiness

The overall manual score improves from 4.163 to 4.267.

### 2. RAG does not fully solve factual-risk problems

Factual accuracy improves only slightly. Some outputs still introduce specific
cases, data visualizations, timelines, named examples, or indicators that need
human verification before being used in a final presentation.

This is especially visible in Qwen outputs, which are often more presentation-ready
but more likely to include vivid, unsupported details.

### 3. DeepSeek is more conservative and factually safer

DeepSeek outputs are slightly less polished but more conservative. Its factual
accuracy score is higher than Qwen in both pure LLM and RAG routes.

This supports using DeepSeek as the primary model when factual reliability and
engineering predictability are more important than rhetorical richness.

### 4. Qwen has stronger presentation expression

Qwen tends to produce richer slide types, stronger teaching-style structure,
and more presentation-friendly phrasing. However, it also introduces more
unverified cases, quotes, timelines, and illustrative data.

This supports using Qwen as a secondary model for creative outline expansion,
provided factual review is applied.

### 5. Page granularity is stable across routes

All sampled outputs maintain the expected page count and generally allocate
one coherent topic per slide. Page granularity mean remains 4.0 for both pure
LLM and RAG outputs.

## Representative Risks Found During Review

- Software engineering outputs may invent course cases or ability-achievement data.
- Alzheimer's disease outputs may over-specify staging frameworks or example patients.
- Football outputs may invent club/team cases, quotes, or visualization designs.
- RAG improves topical grounding but does not prevent all hallucination.

## Engineering Implications

- Use RAG-enhanced generation as the default for professional-domain topics.
- Keep pure LLM as a fallback route when RAG returns HTTP 400 or retrieval context fails.
- Add post-generation factual review for outputs containing:
  - numbers
  - named standards or frameworks
  - clinical staging claims
  - team/player/match cases
  - quoted statements
  - chart values or invented datasets
- Prefer DeepSeek for stable, conservative professional generation.
- Prefer Qwen when presentation style and richer slide layouts matter, but require stricter factual review.

## Generated Assets

- `manual_quality_scores.csv`
- `manual_quality_summary_by_model_route.csv`
- `manual_quality_summary_by_domain_route.csv`
- `manual_quality_summary_by_route.csv`
- `figures/manual_quality_by_model_route.png`
- `figures/manual_quality_metric_profile.png`

