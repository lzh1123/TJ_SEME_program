# Stage 4 Prompt Strategy and Schema Constraint Summary

## Scope

This stage supplements the earlier latency and success-rate analysis with
outline-quality evaluation for prompt strategies and structured-output
constraints.

The deployed `/dsl` endpoint does not expose a free-text/no-schema generation
mode. Therefore, Schema constraint evaluation is based on the system's actual
structured-output chain:

- model output is expected to match a Presentation DSL structure;
- backend validates the result through schema parsing;
- failed JSON/DSL parsing is recorded as schema failure;
- slide-count control is measured by `slide_count_error`;
- page granularity is manually scored.

This means the experiment evaluates the effect of structured output in the
deployed engineering path, but does not claim a strict ablation against an
unconstrained free-text baseline.

## Prompt Strategy Quality Findings

| Strategy | Runs | Success rate | Schema-valid rate | Hierarchy | Logic | Granularity |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 6 | 83.3% | 83.3% | 4.180 | 4.100 | 4.200 |
| stepwise | 6 | 100.0% | 100.0% | 4.317 | 4.217 | 4.183 |
| few-shot | 6 | 66.7% | 66.7% | 4.050 | 3.950 | 4.075 |
| expert-role | 6 | 100.0% | 100.0% | 4.367 | 4.250 | 4.217 |

## Main Conclusions

- Expert-role has the best overall outline quality among the tested prompt strategies.
- Stepwise prompting also performs strongly, especially in hierarchy and logical coherence.
- Few-shot examples can help impose a visible structure in pure LLM mode, but become unstable when combined with RAG context.
- In RAG mode, few-shot produced multiple JSON parsing failures, suggesting that examples plus retrieved context can overload the structured-output instruction.
- Schema constraints are useful for page-count control: successful outputs keep `slide_count_error = 0`.
- Schema constraints do not guarantee successful generation. If the model returns malformed JSON or incompatible DSL fields, the backend still fails with a parsing error.

## Engineering Implications

- Use expert-role or stepwise prompts as default for professional-domain PPT generation.
- Avoid using few-shot prompts together with long RAG context unless prompt length and output schema are carefully controlled.
- Keep structured output validation enabled because it protects downstream rendering and page-count consistency.
- Add schema-repair retry for JSON parsing failures.
- Add prompt-length and context-length checks before invoking the model.

