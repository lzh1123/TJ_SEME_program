from __future__ import annotations

import logging
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
