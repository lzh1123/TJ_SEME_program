from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .embedding import EmbeddingService
from .milvus_client import MilvusStore

logger = logging.getLogger(__name__)


class KnowledgeBase:
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 80

    def __init__(
        self,
        store: MilvusStore,
        embedding: EmbeddingService,
        chunk_size: int = 500,
        chunk_overlap: int = 80,
    ):
        self._store = store
        self._embedding = embedding
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def ensure_collection(self, drop_if_exists: bool = False) -> bool:
        return self._store.ensure_collection(dim=self._embedding.dim, drop_if_exists=drop_if_exists)

    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """Compute SHA256 hash of a file for content-based deduplication."""
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def ingest_text(
        self,
        content: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Ingest text content into the knowledge base.

        Args:
            content: Text content to ingest.
            source: Source identifier (e.g., filename).
            metadata: Optional metadata dict.
            progress_callback: Optional (current, total) progress callback.
            force: If True, delete existing entries for this source before re-ingesting.

        Returns:
            Dict with keys: chunks_inserted, dedup_skipped, action_taken.
        """
        result = {
            "chunks_inserted": 0,
            "dedup_skipped": False,
            "previous_chunks_removed": 0,
            "action_taken": "inserted",
        }

        # ── Dedup check ──
        if self._store.source_exists(source):
            if force:
                # Replace mode: delete old entries, then ingest fresh
                removed = self._store.delete_by_source(source)
                result["previous_chunks_removed"] = removed
                result["action_taken"] = "replaced"
                logger.info(
                    "Dedup: source=%r already existed with %d chunks — REPLACING (force=True)",
                    source, removed,
                )
            else:
                # Skip mode: source already exists, do nothing
                existing_count = self._store.count_by_source(source)
                result["dedup_skipped"] = True
                result["action_taken"] = "skipped"
                logger.info(
                    "Dedup: source=%r already exists with %d chunks — SKIPPING",
                    source, existing_count,
                )
                return result

        # ── Normal ingestion ──
        chunks = self._split_text(content, source, metadata or {})
        if not chunks:
            return result

        texts = [c["text"] for c in chunks]
        batch_size = 32
        total_inserted = 0
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_chunks = chunks[i : i + batch_size]
            embeddings = self._embedding.embed(batch_texts)
            ids = self._store.insert(batch_chunks, embeddings)
            total_inserted += len(ids)
            if progress_callback:
                progress_callback(min(i + batch_size, len(texts)), len(texts))

        result["chunks_inserted"] = total_inserted
        return result

    def ingest_file(
        self,
        file_path: Path,
        metadata: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Ingest a file into the knowledge base with deduplication.

        Dedup strategy (two-layer):
          1. Source-based: checks if the filename already exists in Milvus.
          2. Content-based: stores SHA256 hash in metadata for future hash-based dedup.

        Args:
            file_path: Path to the file.
            metadata: Optional metadata dict.
            progress_callback: Optional progress callback.
            force: If True, delete existing entries and re-ingest even if source exists.

        Returns:
            Dict with keys: chunks_inserted, dedup_skipped, action_taken, file_hash.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower()
        content = self._read_file(path, suffix)
        if not content:
            return {
                "chunks_inserted": 0,
                "dedup_skipped": False,
                "previous_chunks_removed": 0,
                "action_taken": "empty_content",
                "file_hash": "",
            }

        # Compute content hash
        try:
            file_hash = self._compute_file_hash(path)
        except Exception:
            file_hash = ""

        meta = metadata or {}
        meta.setdefault("filename", path.name)
        meta["sha256"] = file_hash

        result = self.ingest_text(
            content,
            source=path.name,
            metadata=meta,
            progress_callback=progress_callback,
            force=force,
        )
        result["file_hash"] = file_hash
        return result

    def remove_source(self, source: str) -> int:
        return self._store.delete_by_source(source)

    def get_stats(self) -> Dict[str, Any]:
        return self._store.get_collection_stats()

    def _read_file(self, path: Path, suffix: str) -> str:
        if suffix == ".txt" or suffix == ".md":
            return path.read_text(encoding="utf-8")
        if suffix == ".pdf":
            return self._read_pdf(path)
        if suffix == ".docx":
            return self._read_docx(path)
        return ""

    def _read_pdf(self, path: Path) -> str:
        try:
            import fitz

            doc = fitz.open(str(path))
            parts = []
            for page in doc:
                text = page.get_text()
                if text:
                    parts.append(text)
            doc.close()
            return "\n\n".join(parts)
        except ImportError:
            return ""

    def _read_docx(self, path: Path) -> str:
        try:
            from docx import Document

            doc = Document(str(path))
            parts = []
            for p in doc.paragraphs:
                if p.text.strip():
                    parts.append(p.text)
            return "\n\n".join(parts)
        except ImportError:
            return ""

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _split_text(
        self,
        content: str,
        source: str,
        metadata: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        if not paragraphs:
            return []

        chunks = []
        current = ""
        chunk_idx = 0
        for para in paragraphs:
            if len(current) + len(para) + 1 <= self._chunk_size:
                current = f"{current} {para}".strip() if current else para
            else:
                if current:
                    chunks.append(self._make_chunk(current, source, chunk_idx, metadata))
                    chunk_idx += 1
                current = para
            while len(current) > self._chunk_size:
                split_at = current.rfind("。", 0, self._chunk_size)
                if split_at < self._chunk_size // 2:
                    split_at = self._chunk_size
                head = current[: split_at + 1]
                chunks.append(self._make_chunk(head, source, chunk_idx, metadata))
                chunk_idx += 1
                current = current[split_at + 1 :].lstrip()

        if current.strip():
            chunks.append(self._make_chunk(current.strip(), source, chunk_idx, metadata))

        return chunks

    def _make_chunk(
        self,
        text: str,
        source: str,
        chunk_index: int,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "text": self._clean_text(text),
            "source": source,
            "chunk_index": chunk_index,
            "metadata": metadata,
        }
