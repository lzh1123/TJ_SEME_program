# Stage 2 Experiment Summary

## Scope

This stage extends the first baseline experiment by excluding Kimi and focusing
on DeepSeek and Qwen stability, latency, and prompt-strategy behavior.

## Completed Runs

### Combined stability experiment

- Endpoint: `http://119.3.125.141/dsl`
- Models: DeepSeek, Qwen
- Retrieval routes: pure LLM, RAG-enhanced
- Domains: software engineering, Alzheimer's disease, football
- Scenarios: short topic, long input, professional topic
- Total runs: 108
  - 36 baseline runs from stage 1
  - 72 additional stability-repeat runs from stage 2
- Repeats per condition: 3

### Prompt strategy expanded experiment

- Model: DeepSeek
- Domains: software engineering, Alzheimer's disease, football
- Scenario: short topic
- Retrieval routes: pure LLM, RAG-enhanced
- Prompt strategies: baseline, stepwise, few-shot, expert-role
- Total runs: 24

## Combined Stability Results

| Model | Route | Runs | Success rate | Schema-valid rate | Mean latency | Latency std |
|---|---:|---:|---:|---:|---:|---:|
| DeepSeek | Pure LLM | 27 | 100.0% | 100.0% | 56.000s | 15.188s |
| DeepSeek | RAG-enhanced | 27 | 96.3% | 96.3% | 57.468s | 14.870s |
| Qwen | Pure LLM | 27 | 100.0% | 100.0% | 70.738s | 18.170s |
| Qwen | RAG-enhanced | 27 | 96.3% | 96.3% | 72.313s | 18.921s |

Key observations:

- Pure LLM was fully stable for DeepSeek and Qwen across the current 54 pure-LLM runs.
- RAG-enhanced generation introduced a small failure risk: one failed run for DeepSeek and one failed run for Qwen.
- DeepSeek remained faster than Qwen in both pure LLM and RAG-enhanced routes.
- RAG added little average latency to DeepSeek but increased Qwen's average latency by about 1.6 seconds compared with Qwen pure LLM.
- Slide count error remained 0.0 across model-route summaries, which means the requested page-count preset was respected in successful outputs.

## Domain-Level Stability Results

| Domain | Route | Runs | Success rate | Mean latency |
|---|---:|---:|---:|---:|
| Alzheimer's disease | Pure LLM | 18 | 100.0% | 63.071s |
| Alzheimer's disease | RAG-enhanced | 18 | 94.4% | 59.867s |
| Football | Pure LLM | 18 | 100.0% | 67.508s |
| Football | RAG-enhanced | 18 | 100.0% | 71.740s |
| Software engineering | Pure LLM | 18 | 100.0% | 59.527s |
| Software engineering | RAG-enhanced | 18 | 94.4% | 63.064s |

Key observations:

- Football RAG had no failures in the combined stability experiment but had higher average latency than pure LLM.
- Alzheimer's disease and software engineering each had one RAG-enhanced failure.
- Pure LLM stayed fully successful across all three domains.

## Stability Failure Cases

| Case | Model | Route | Latency | HTTP status | Error |
|---|---|---|---:|---:|---|
| SE_PRO_01 | DeepSeek | RAG-enhanced | 49.222s | 400 | HTTPError: HTTP Error 400: Bad Request |
| AD_LONG_01 | Qwen | RAG-enhanced | 18.607s | 400 | HTTPError: HTTP Error 400: Bad Request |

Interpretation:

- The failures are route-specific rather than model-wide failures.
- Both failures occurred in RAG-enhanced mode, suggesting the retrieval or context-injection path needs engineering hardening.
- The pure LLM route can be used as a fallback path when RAG fails.

## Prompt Strategy Expanded Results

| Prompt strategy | Route | Runs | Success rate | Schema-valid rate | Mean latency |
|---|---:|---:|---:|---:|---:|
| baseline | Pure LLM | 3 | 100.0% | 100.0% | 46.566s |
| baseline | RAG-enhanced | 3 | 66.7% | 66.7% | 229.457s |
| stepwise | Pure LLM | 3 | 100.0% | 100.0% | 47.741s |
| stepwise | RAG-enhanced | 3 | 100.0% | 100.0% | 52.940s |
| few-shot | Pure LLM | 3 | 100.0% | 100.0% | 57.440s |
| few-shot | RAG-enhanced | 3 | 33.3% | 33.3% | 50.905s |
| expert-role | Pure LLM | 3 | 100.0% | 100.0% | 43.529s |
| expert-role | RAG-enhanced | 3 | 100.0% | 100.0% | 43.075s |

Key observations:

- In pure LLM mode, all prompt strategies succeeded.
- In RAG-enhanced mode, stepwise and expert-role prompts were the most stable in this expanded pilot.
- The baseline RAG strategy had one very long failed run, producing a high mean latency and very high variance.
- Few-shot with RAG was unstable in this small sample, with two failed runs out of three.
- Expert-role had both high success and low mean latency in this pilot, making it a promising default prompt style for professional topic generation.

## Generated Data Assets

- Stability repeats:
  - `Knowledge base/Report Assets/stability_repeats_results.csv`
  - `Knowledge base/Report Assets/stability_repeats_errors.csv`
- Combined stability summaries:
  - `Knowledge base/Report Assets/combined_stability_summary_by_model_route.csv`
  - `Knowledge base/Report Assets/combined_stability_summary_by_domain_route.csv`
  - `Knowledge base/Report Assets/combined_stability_summary_by_scenario_route.csv`
  - `Knowledge base/Report Assets/combined_stability_summary_by_case_model_route.csv`
- Prompt expanded summaries:
  - `Knowledge base/Report Assets/prompt_strategy_expanded_results.csv`
  - `Knowledge base/Report Assets/prompt_strategy_expanded_errors.csv`
  - `Knowledge base/Report Assets/prompt_expanded_summary_by_prompt_strategy_route.csv`
- Figures:
  - `Knowledge base/Report Assets/figures/combined_stability_latency_by_model_route.png`
  - `Knowledge base/Report Assets/figures/combined_stability_success_rate_by_model_route.png`
  - `Knowledge base/Report Assets/figures/combined_stability_latency_by_domain_route.png`
  - `Knowledge base/Report Assets/figures/prompt_expanded_prompt_strategy_latency.png`
  - `Knowledge base/Report Assets/figures/prompt_expanded_success_rate_by_model_route.png`

## Technical Selection Implications

- Recommended primary model for current deployment: DeepSeek, because it has lower average latency than Qwen while maintaining comparable success rate.
- Recommended fallback model: Qwen, because it is broadly successful but slower.
- Recommended default route: RAG-enhanced for professional-domain generation when factual grounding is important, with pure LLM fallback on RAG failure.
- Recommended prompt style for RAG: expert-role or stepwise, based on the expanded prompt experiment.
- Current risk: RAG-enhanced generation has occasional HTTP 400 failures and should be wrapped with retry, error capture, and pure-LLM fallback.

## Next Step

Manual quality scoring is now needed. Suggested sample:

- 12 outputs from the combined stability experiment:
  - 3 domains
  - pure LLM vs. RAG
  - DeepSeek vs. Qwen
- 8 outputs from prompt strategy experiment:
  - DeepSeek only
  - pure LLM vs. RAG
  - stepwise and expert-role

Manual scoring should use the rubric in `experiment_protocol.md`:

- structure rationality
- logical coherence
- page granularity
- information density
- factual accuracy
- domain terminology
- presentation readiness
