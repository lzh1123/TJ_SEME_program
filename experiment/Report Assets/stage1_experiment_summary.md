# Stage 1 Experiment Summary

## Completed Runs

### Main baseline experiment

- Endpoint: `http://119.3.125.141/dsl`
- Test cases: 9
  - 3 domains: software engineering, Alzheimer's disease, football
  - 3 scenarios per domain: short topic, long input, professional topic
- Models: DeepSeek, Qwen
- Routes: pure LLM, RAG-enhanced
- Total runs: 36
- Success rate: 100%
- Schema-valid rate: 100%

### Model availability pilot

Kimi was tested on the same short-topic case before the main baseline run.

| Model | Route | Result | Latency |
|---|---|---|---|
| DeepSeek | Pure LLM | Success | 43.726s |
| DeepSeek | RAG-enhanced | Success | 41.162s |
| Qwen | Pure LLM | Success | 47.704s |
| Qwen | RAG-enhanced | Success | 49.167s |
| Kimi | Pure LLM | Failed | 300.011s timeout |
| Kimi | RAG-enhanced | Failed | 269.489s, HTTP 400 |

For the main baseline experiment, Kimi was excluded to avoid blocking the run.
It should be reported as a current availability and latency-risk issue unless
later reruns confirm recovery.

## Main Latency Findings

| Model | Route | Runs | Success rate | Mean latency | Latency std |
|---|---:|---:|---:|---:|---:|
| DeepSeek | Pure LLM | 9 | 1.0 | 60.709s | 13.719s |
| DeepSeek | RAG-enhanced | 9 | 1.0 | 57.865s | 7.991s |
| Qwen | Pure LLM | 9 | 1.0 | 65.157s | 18.695s |
| Qwen | RAG-enhanced | 9 | 1.0 | 74.795s | 16.202s |

Initial interpretation:

- Both DeepSeek and Qwen completed all baseline cases successfully.
- DeepSeek had lower mean latency than Qwen in this run.
- RAG did not always increase latency. For DeepSeek, RAG-enhanced generation was slightly faster on average in this sample; for Qwen, RAG-enhanced generation was slower.
- Qwen showed a higher latency maximum, especially in the football professional-topic RAG case.

## Domain Latency Findings

| Domain | Route | Runs | Mean latency |
|---|---:|---:|---:|
| Alzheimer's disease | Pure LLM | 6 | 67.613s |
| Alzheimer's disease | RAG-enhanced | 6 | 66.441s |
| Football | Pure LLM | 6 | 64.363s |
| Football | RAG-enhanced | 6 | 71.133s |
| Software engineering | Pure LLM | 6 | 56.823s |
| Software engineering | RAG-enhanced | 6 | 61.418s |

Initial interpretation:

- Alzheimer's disease had similar latency between pure LLM and RAG.
- Football and software engineering showed higher average latency under RAG.
- The current sample is suitable for stage-1 latency comparison, but repeated runs are still needed for final stability claims.

## Prompt Strategy Pilot

Single-case pilot:

- Case: `SE_SHORT_01`
- Model: DeepSeek
- Route: Pure LLM
- Repeats: 1 per strategy

| Strategy | Success | Latency | Slide count |
|---|---:|---:|---:|
| baseline | true | 34.195s | 9 |
| stepwise | true | 37.641s | 9 |
| few_shot | true | 40.180s | 9 |
| expert_role | true | 40.177s | 9 |

Initial interpretation:

- All four prompt strategies returned valid structured output.
- Strategy-enriched prompts increased latency slightly in this pilot.
- Slide count remained stable at 9, matching the short-page expectation.
- Quality scoring still requires manual review of the raw outputs.

## Generated Assets

- Raw outputs: `Knowledge base/Report Assets/raw_outputs/`
- Main results: `Knowledge base/Report Assets/experiment_results.csv`
- Model availability pilot: `Knowledge base/Report Assets/model_availability_pilot.csv`
- Prompt pilot: `Knowledge base/Report Assets/prompt_strategy_pilot_results.csv`
- Summary tables:
  - `summary_by_model_route.csv`
  - `summary_by_domain_route.csv`
  - `summary_by_scenario_route.csv`
  - `summary_by_case_model_route.csv`
- Figures:
  - `figures/latency_by_model_route.png`
  - `figures/latency_by_model_route.svg`
  - `figures/latency_by_domain_route.png`
  - `figures/latency_by_domain_route.svg`

## Recommended Next Runs

1. Repeat the main baseline experiment 3 times for DeepSeek and Qwen to support stronger stability claims.
2. Rerun Kimi separately with a longer timeout or inspect backend error details before including it in quality comparison.
3. Expand prompt strategy experiments to all three domains.
4. Add manual quality scoring for representative outputs using the quality rubric.
5. Generate final charts for success rate, latency, slide-count stability, and manual quality score.
