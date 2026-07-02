# PPT Outline Generation Experiment Protocol

## Objective

Evaluate the deployed PPT outline generation system through controlled
experiments covering:

- Pure LLM vs. RAG-enhanced generation.
- Short topic input, long document-like input, and professional-domain topic.
- Prompt strategy variants through user-facing prompt formulations.
- Model comparison across the currently deployed providers.
- Quality, stability, and latency.

## Endpoint

- URL: `http://119.3.125.141/dsl`
- Method: `POST`
- Payload example:

```json
{
  "topic": "软件工程介绍",
  "theme": null,
  "use_rag": false,
  "modelProvider": "deepseek",
  "pageCountPreset": "medium"
}
```

## Model Providers

The deployed frontend exposes these providers:

| Provider | Display name | Model shown in UI |
|---|---|---|
| deepseek | DeepSeek | Deepseek-V4-pro |
| qwen | Qwen | qwen-plus |
| kimi | Kimi | kimi-k2.6 |

## Experimental Factors

| Factor | Levels |
|---|---|
| Domain | software_engineering, alzheimer, football |
| Scenario | short_topic, long_input, professional_topic |
| Retrieval route | pure_llm, rag_enhanced |
| Model | deepseek, qwen, kimi |
| Page count preset | short, medium |

## Prompt Strategy Variants

The current public `/dsl` endpoint exposes only the user topic field rather
than a separate prompt-template selector. Therefore prompt strategy is tested
by controlled topic formulations:

| Strategy | Implementation through topic field |
|---|---|
| baseline | Direct task phrase. |
| stepwise | Ask the model to first organize logic, then generate outline. |
| few_shot | Include a compact expected outline style example in the topic. |
| expert_role | Ask from a domain expert / teaching perspective. |

## Metrics

### System Metrics

- `success`: request completed and returned valid JSON.
- `latency_seconds`: wall-clock request time.
- `http_status`: HTTP status code when available.
- `output_size_chars`: response body length.
- `slide_count`: number of slides returned.

### Stability Metrics

- `schema_valid`: whether response contains a top-level outline object.
- `slide_count_error`: absolute difference between expected slide range and actual slide count.
- `title_present_rate`: whether title is present.
- `failure_rate`: failed runs / total runs for the same condition.
- `latency_mean`, `latency_std`, `latency_p95`.

### Quality Metrics for Manual Review

Manual review uses a 1-5 scale:

| Metric | Meaning |
|---|---|
| structure_rationality | Outline hierarchy and section arrangement are reasonable. |
| logical_coherence | Slides follow a coherent narrative. |
| page_granularity | Each slide has appropriate scope and density. |
| information_density | Content is neither empty nor overloaded. |
| factual_accuracy | Domain facts are accurate. |
| domain_terminology | Professional terms are used correctly. |
| presentation_readiness | The outline is suitable for PPT creation. |

## Repetition Rule

For the final experiment, each condition should be repeated at least 3 times
to estimate stability and latency variance.

## Output Files

- Raw JSON responses: `Knowledge base/Report Assets/raw_outputs/`
- Experiment logs: `Knowledge base/Report Assets/experiment_results.csv`
- Error logs: `Knowledge base/Report Assets/experiment_errors.csv`

