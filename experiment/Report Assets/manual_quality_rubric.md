# Manual Quality Scoring Rubric

Scoring range: 1-5. Higher is better.

| Metric | 1 | 3 | 5 |
|---|---|---|---|
| structure_rationality | Disordered outline, missing major sections | Mostly reasonable but uneven | Clear hierarchy and complete section arrangement |
| logical_coherence | Slides are disconnected | Basic narrative flow | Strong progression from background to method, case, and conclusion |
| page_granularity | Slides are too broad or fragmented | Mostly acceptable page scope | Each slide has a clear, focused role |
| information_density | Empty or generic content | Moderate amount of useful content | Rich but not overloaded |
| factual_accuracy | Obvious factual errors or unsupported claims | Mostly correct with some hallucination risk | Accurate and grounded in domain knowledge |
| domain_terminology | Few or incorrect technical terms | Basic terms used correctly | Professional terms are accurate and contextually appropriate |
| presentation_readiness | Hard to use as a PPT outline | Usable after moderate editing | Directly usable for PPT production |

## Scoring Notes

- Scores reflect the generated outline content, not the final rendered PPT.
- Factual accuracy is scored conservatively when the outline introduces specific cases, statistics, timelines, or named frameworks that are not clearly grounded in the prompt or knowledge base.
- RAG-enhanced outputs are expected to improve domain grounding, but they can still lose points if they introduce fabricated examples or over-specific claims.
- All sampled outputs use the professional-topic scenario to keep the comparison controlled across model and retrieval route.

