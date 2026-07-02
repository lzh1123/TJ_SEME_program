from __future__ import annotations

import pytest

from ppt_backend.services.rag.document_parser import (
    DocumentParseError,
    compact_document_text,
    parse_document,
)


def test_text_document_parsing_and_long_document_compaction(tmp_path):
    text_path = tmp_path / "source.txt"
    text_path.write_text("Line one\nLine two", encoding="utf-8")
    assert parse_document(text_path, ".txt") == "Line one\nLine two"

    long_text = "\n".join(f"section {i}: validated content" for i in range(1000))
    compact = compact_document_text(long_text, max_chars=600)
    assert len(compact) < len(long_text)
    assert "[content truncated]" in compact
    assert compact.startswith("section 0")


def test_unsupported_document_suffix_is_rejected(tmp_path):
    with pytest.raises(DocumentParseError):
        parse_document(tmp_path / "bad.exe", ".exe")
