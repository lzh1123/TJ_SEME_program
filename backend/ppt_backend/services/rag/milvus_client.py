from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from pymilvus import DataType, MilvusClient

logger = logging.getLogger(__name__)


class MilvusStore:
    COLLECTION_NAME = "ppt_knowledge_base"

    def __init__(self, uri: str = "http://localhost:19530", db_name: str = "default"):
        self._uri = uri
        self._db_name = db_name
        self._client: Optional[MilvusClient] = None

    @property
    def client(self) -> MilvusClient:
        if self._client is None:
            self._client = MilvusClient(uri=self._uri, db_name=self._db_name)
            logger.info("Created new MilvusClient (uri=%s)", self._uri)
        else:
            # Health check: lazy reconnection if the connection was closed
            try:
                self._client.list_collections()
            except Exception:
                logger.warning("MilvusClient connection appears closed, reconnecting...")
                try:
                    self._client.close()
                except Exception:
                    pass
                self._client = MilvusClient(uri=self._uri, db_name=self._db_name)
                logger.info("Reconnected MilvusClient (uri=%s)", self._uri)
        return self._client

    @property
    def available(self) -> bool:
        try:
            self.client.list_collections()
            return True
        except Exception:
            return False

    def ensure_collection(self, dim: int, drop_if_exists: bool = False) -> bool:
        if self.client.has_collection(self.COLLECTION_NAME):
            if drop_if_exists:
                logger.info("Dropping existing collection %s", self.COLLECTION_NAME)
                self.client.drop_collection(self.COLLECTION_NAME)
            else:
                logger.debug("Collection %s already exists, skipping creation", self.COLLECTION_NAME)
                return False

        logger.info("Creating collection %s (dim=%d)", self.COLLECTION_NAME, dim)
        schema = self.client.create_schema(
            auto_id=True,
            enable_dynamic_field=False,
        )
        schema.add_field(
            field_name="id",
            datatype=DataType.INT64,
            is_primary=True,
            auto_id=True,
        )
        schema.add_field(
            field_name="text",
            datatype=DataType.VARCHAR,
            max_length=65535,
            enable_analyzer=True,
            analyzer_params={"type": "chinese"},
        )
        schema.add_field(
            field_name="embedding",
            datatype=DataType.FLOAT_VECTOR,
            dim=dim,
        )
        schema.add_field(
            field_name="source",
            datatype=DataType.VARCHAR,
            max_length=512,
        )
        schema.add_field(
            field_name="chunk_index",
            datatype=DataType.INT64,
        )
        schema.add_field(
            field_name="metadata",
            datatype=DataType.JSON,
        )

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="AUTOINDEX",
            metric_type="IP",
        )
        index_params.add_index(
            field_name="id",
            index_type="STL_SORT",
        )

        self.client.create_collection(
            collection_name=self.COLLECTION_NAME,
            schema=schema,
            index_params=index_params,
        )
        self.client.load_collection(self.COLLECTION_NAME)
        logger.info("Collection %s created and loaded successfully", self.COLLECTION_NAME)
        return True

    def insert(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> List[int]:
        data = []
        sources = set()
        for chunk, emb in zip(chunks, embeddings):
            src = chunk.get("source", "")
            sources.add(src)
            data.append({
                "text": chunk.get("text", ""),
                "embedding": emb,
                "source": src,
                "chunk_index": chunk.get("chunk_index", 0),
                "metadata": chunk.get("metadata", {}),
            })
        logger.info("Inserting %d chunks (sources=%s) into %s", len(data), sorted(sources), self.COLLECTION_NAME)
        result = self.client.insert(collection_name=self.COLLECTION_NAME, data=data)
        ids = result.get("ids", [])
        logger.info("Inserted %d chunks, got %d IDs", len(data), len(ids))
        return ids

    def _ensure_loaded(self) -> None:
        """Ensure the collection is loaded into memory (required for queries and deletes)."""
        try:
            self.client.load_collection(self.COLLECTION_NAME)
        except Exception:
            logger.debug("Collection %s load skipped (already loaded or unavailable)", self.COLLECTION_NAME)

    def _escape_filter_string(self, value: str) -> str:
        """Escape a string value for safe use in Milvus filter expressions.

        Milvus uses double-quoted strings in filter expressions. We must escape
        backslashes and double quotes to avoid breaking the expression syntax.
        """
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _get_ids_by_source(self, source: str) -> List[int]:
        """Get all entity IDs for a given source. Returns empty list if none found."""
        self._ensure_loaded()
        try:
            escaped = self._escape_filter_string(source)
            filter_expr = f'source == "{escaped}"'
            logger.debug("Querying IDs by source=%r (filter=%s)", source, filter_expr)
            result = self.client.query(
                collection_name=self.COLLECTION_NAME,
                filter=filter_expr,
                output_fields=["id"],
                limit=10000,
            )
            ids = [int(r["id"]) for r in result if "id" in r]
            logger.debug("Found %d ids for source=%r", len(ids), source)
            return ids
        except Exception:
            logger.exception("Failed to query IDs for source=%r", source)
            return []

    def source_exists(self, source: str) -> bool:
        """Check if a source already has entries in the collection."""
        ids = self._get_ids_by_source(source)
        exists = len(ids) > 0
        logger.debug("source_exists(%r) = %s (%d chunks)", source, exists, len(ids))
        return exists

    def count_by_source(self, source: str) -> int:
        """Count how many chunks exist for a given source."""
        count = len(self._get_ids_by_source(source))
        logger.debug("count_by_source(%r) = %d", source, count)
        return count

    def delete_by_source(self, source: str) -> int:
        """Delete all entries for a given source.
        Uses ID-based deletion (query IDs first, then delete by IDs)
        which is more reliable than filter-based delete in Milvus 3.x.

        Returns the actual number of entities deleted (from Milvus response).
        """
        self._ensure_loaded()
        ids = self._get_ids_by_source(source)
        if not ids:
            # Double-check: if source still appears via list_sources-style query,
            # then _get_ids_by_source failed — log a warning.
            logger.warning(
                "No IDs found for source=%r — the source may not exist, "
                "or the query may have failed (check above for exceptions).",
                source,
            )
            return 0

        expected = len(ids)
        try:
            result = self.client.delete(
                collection_name=self.COLLECTION_NAME,
                ids=ids,
            )
            delete_count = self._parse_delete_count(result, expected)
            if delete_count != expected:
                logger.warning(
                    "Delete mismatch for source=%r: expected %d, actual delete_count=%d",
                    source, expected, delete_count,
                )
            return delete_count
        except Exception as e:
            logger.exception("ID-based delete failed for source=%r, trying filter-based fallback", source)
            # Fallback: try filter-based delete
            try:
                escaped = self._escape_filter_string(source)
                result = self.client.delete(
                    collection_name=self.COLLECTION_NAME,
                    filter=f'source == "{escaped}"',
                )
                delete_count = self._parse_delete_count(result, expected)
                logger.info(
                    "Filter-based fallback delete for source=%r: delete_count=%d",
                    source, delete_count,
                )
                return delete_count
            except Exception:
                logger.exception("Filter-based delete also failed for source=%r", source)
                raise e

    @staticmethod
    def _parse_delete_count(result: Any, fallback: int) -> int:
        """Extract delete_count from pymilvus delete result.

        pymilvus 3.x returns a dict like {'delete_count': N, 'cost': ...}.
        If we can't parse it, fall back to the expected count.
        """
        if isinstance(result, dict):
            count = result.get("delete_count")
            if isinstance(count, int):
                return count
        logger.debug("Could not parse delete_count from result: %r", result)
        return fallback

    def hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 10,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        logger.debug(
            "hybrid_search: query=%r top_k=%d source_filter=%r",
            query_text[:80], top_k, source_filter,
        )
        dense_hits = self._dense_search(query_embedding, top_k * 2, source_filter)
        sparse_hits = self._keyword_search(query_text, top_k * 2, source_filter)
        fused = self._rrf_fuse(dense_hits, sparse_hits, top_k)
        logger.debug("hybrid_search: dense=%d sparse=%d fused=%d final=%d",
                      len(dense_hits), len(sparse_hits), len(fused), min(top_k, len(fused)))
        return fused

    def vector_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        logger.debug("vector_search: top_k=%d source_filter=%r", top_k, source_filter)
        result = self._dense_search(query_embedding, top_k, source_filter)
        logger.debug("vector_search: returned %d hits", len(result))
        return result

    def keyword_search(
        self,
        query_text: str,
        top_k: int = 10,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        logger.debug("keyword_search: query=%r top_k=%d source_filter=%r",
                      query_text[:80], top_k, source_filter)
        result = self._keyword_search(query_text, top_k, source_filter)
        logger.debug("keyword_search: returned %d hits", len(result))
        return result

    def _dense_search(
        self,
        query_embedding: List[float],
        top_k: int,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        filter_expr = None
        if source_filter:
            escaped = self._escape_filter_string(source_filter)
            filter_expr = f'source like "%{escaped}%"'

        logger.debug("_dense_search: top_k=%d filter=%r", top_k, filter_expr)
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            data=[query_embedding],
            anns_field="embedding",
            limit=top_k,
            output_fields=["id", "text", "source", "chunk_index", "metadata"],
            filter=filter_expr,
        )
        hits = []
        for result in results:
            for hit in result:
                entity = hit.get("entity", hit)
                hits.append({
                    "id": entity.get("id"),
                    "text": entity.get("text", ""),
                    "source": entity.get("source", ""),
                    "chunk_index": entity.get("chunk_index", 0),
                    "metadata": entity.get("metadata", {}),
                    "score": hit.get("distance", hit.get("score", 0.0)),
                })
        logger.debug("_dense_search: returned %d hits (top score=%.4f)",
                      len(hits), hits[0]["score"] if hits else 0.0)
        return hits

    def _keyword_search(
        self,
        query_text: str,
        top_k: int,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        escaped = self._escape_filter_string(query_text)
        filter_parts = [f'text like "%{escaped}%"']
        if source_filter:
            escaped_src = self._escape_filter_string(source_filter)
            filter_parts.append(f'source like "%{escaped_src}%"')
        filter_expr = " and ".join(filter_parts)

        logger.debug("_keyword_search: query=%r filter=%r top_k=%d",
                      query_text[:80], filter_expr, top_k)
        results = self.client.query(
            collection_name=self.COLLECTION_NAME,
            filter=filter_expr,
            output_fields=["id", "text", "source", "chunk_index", "metadata"],
            limit=top_k,
        )
        hits = []
        for entity in results:
            hits.append({
                "id": entity.get("id"),
                "text": entity.get("text", ""),
                "source": entity.get("source", ""),
                "chunk_index": entity.get("chunk_index", 0),
                "metadata": entity.get("metadata", {}),
                "score": 1.0,
            })
        logger.debug("_keyword_search: returned %d hits", len(hits))
        return hits

    def _rrf_fuse(
        self,
        list_a: List[Dict[str, Any]],
        list_b: List[Dict[str, Any]],
        top_k: int,
        rrf_k: int = 60,
    ) -> List[Dict[str, Any]]:
        scores: Dict[int, float] = {}
        items: Dict[int, Dict[str, Any]] = {}

        for rank, item in enumerate(list_a):
            key = item.get("id") or hash(item.get("text", ""))
            scores[key] = scores.get(key, 0) + 1.0 / (rrf_k + rank + 1)
            items[key] = item

        for rank, item in enumerate(list_b):
            key = item.get("id") or hash(item.get("text", ""))
            scores[key] = scores.get(key, 0) + 1.0 / (rrf_k + rank + 1)
            if key not in items:
                items[key] = item

        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [items[key] for key, _ in sorted_items[:top_k]]

    def get_collection_stats(self) -> Dict[str, Any]:
        if not self.client.has_collection(self.COLLECTION_NAME):
            logger.debug("get_collection_stats: collection %s does not exist", self.COLLECTION_NAME)
            return {"exists": False, "num_entities": 0}
        stats = self.client.get_collection_stats(self.COLLECTION_NAME)
        row_count = stats.get("row_count", 0)
        logger.debug("get_collection_stats: row_count=%s", row_count)
        return {"exists": True, "num_entities": row_count}

    def find_by_hash(self, sha256_hash: str) -> Optional[str]:
        """Check if any entity has this SHA256 hash in metadata.
        Returns the source name if found, None otherwise."""
        if not sha256_hash:
            return None
        self._ensure_loaded()
        logger.debug("find_by_hash: searching for hash prefix=%s", sha256_hash[:16])
        try:
            escaped = self._escape_filter_string(sha256_hash)
            result = self.client.query(
                collection_name=self.COLLECTION_NAME,
                filter=f'metadata like "%{escaped}%"',
                output_fields=["source", "metadata"],
                limit=1,
            )
            if result:
                meta = result[0].get("metadata", {})
                if isinstance(meta, dict) and meta.get("sha256") == sha256_hash:
                    found_source = result[0].get("source")
                    logger.info("find_by_hash: dedup match — source=%r", found_source)
                    return found_source
            logger.debug("find_by_hash: no match for hash prefix=%s", sha256_hash[:16])
            return None
        except Exception:
            logger.exception("Failed to query by hash prefix=%s", sha256_hash[:16])
            return None

    def list_sources(self) -> List[Dict[str, Any]]:
        """List distinct sources with their chunk counts and latest metadata."""
        if not self.client.has_collection(self.COLLECTION_NAME):
            logger.debug("list_sources: collection %s does not exist", self.COLLECTION_NAME)
            return []
        self._ensure_loaded()
        try:
            logger.debug("list_sources: querying all entities")
            results = self.client.query(
                collection_name=self.COLLECTION_NAME,
                filter="id >= 0",
                output_fields=["source", "chunk_index", "metadata"],
                limit=10000,
            )
            logger.debug("list_sources: got %d raw entities", len(results))
        except Exception:
            logger.exception("Failed to list sources from Milvus")
            return []

        # Group by source in Python
        sources: Dict[str, Dict[str, Any]] = {}
        for entity in results:
            source = entity.get("source", "unknown")
            if source not in sources:
                sources[source] = {
                    "source": source,
                    "chunks": 0,
                    "filename": source,
                }
                # Extract filename from metadata if available
                meta = entity.get("metadata", {})
                if isinstance(meta, dict) and meta.get("filename"):
                    sources[source]["filename"] = meta["filename"]
            sources[source]["chunks"] += 1

        sorted_sources = sorted(sources.values(), key=lambda x: x["chunks"], reverse=True)
        logger.debug("list_sources: %d distinct sources, total chunks=%d",
                      len(sorted_sources), sum(s["chunks"] for s in sorted_sources))
        return sorted_sources

    def close(self):
        logger.debug("Closing MilvusClient")
        self._client = None
