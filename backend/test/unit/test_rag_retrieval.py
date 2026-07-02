from __future__ import annotations

from ppt_backend.services.rag.retrieval import HybridRetriever


def test_rrf_retrieval_fuses_local_and_web_results_with_local_weight_priority():
    retriever = HybridRetriever(
        store=object(),
        embedding=object(),
        web_search=object(),
        web_ratio=0.4,
    )
    fused = retriever._rrf_fuse(
        web_results=[
            {"url": "https://example.com/a", "text": "web high level", "source": "web:a"},
            {"url": "https://example.com/b", "text": "web backup", "source": "web:b"},
        ],
        local_results=[
            {"text": "local exact evidence", "source": "kb:a"},
            {"text": "local secondary evidence", "source": "kb:b"},
        ],
        top_k=3,
    )

    assert len(fused) == 3
    assert fused[0]["source"] == "kb:a"
    assert any(item["source"].startswith("web") for item in fused)
