from __future__ import annotations

from typing import Any, Dict, List, Optional

from pymilvus import DataType, MilvusClient


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
                self.client.drop_collection(self.COLLECTION_NAME)
            else:
                return False

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
        return True

    def insert(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> List[int]:
        data = []
        for chunk, emb in zip(chunks, embeddings):
            data.append({
                "text": chunk.get("text", ""),
                "embedding": emb,
                "source": chunk.get("source", ""),
                "chunk_index": chunk.get("chunk_index", 0),
                "metadata": chunk.get("metadata", {}),
            })
        result = self.client.insert(collection_name=self.COLLECTION_NAME, data=data)
        return result.get("ids", [])

    def _ensure_loaded(self) -> None:
        """Ensure the collection is loaded into memory (required for queries and deletes)."""
        try:
            self.client.load_collection(self.COLLECTION_NAME)
        except Exception:
            pass  # Already loaded or not available

    def _get_ids_by_source(self, source: str) -> List[int]:
        """Get all entity IDs for a given source. Returns empty list if none found."""
        self._ensure_loaded()
        try:
            result = self.client.query(
                collection_name=self.COLLECTION_NAME,
                filter=f'source == "{source}"',
                output_fields=["id"],
                limit=10000,
            )
            return [int(r["id"]) for r in result if "id" in r]
        except Exception:
            return []

    def source_exists(self, source: str) -> bool:
        """Check if a source already has entries in the collection."""
        ids = self._get_ids_by_source(source)
        return len(ids) > 0

    def count_by_source(self, source: str) -> int:
        """Count how many chunks exist for a given source."""
        return len(self._get_ids_by_source(source))

    def delete_by_source(self, source: str) -> int:
        """Delete all entries for a given source.
        Uses ID-based deletion (query IDs first, then delete by IDs)
        which is more reliable than filter-based delete in Milvus 3.x."""
        self._ensure_loaded()
        ids = self._get_ids_by_source(source)
        if not ids:
            return 0

        try:
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                ids=ids,
            )
            return len(ids)
        except Exception as e:
            # Fallback: try filter-based delete
            try:
                self.client.delete(
                    collection_name=self.COLLECTION_NAME,
                    filter=f'source == "{source}"',
                )
                return len(ids)  # Assume success if no exception
            except Exception:
                raise e

    def hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 10,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        dense_hits = self._dense_search(query_embedding, top_k * 2, source_filter)
        sparse_hits = self._keyword_search(query_text, top_k * 2, source_filter)
        return self._rrf_fuse(dense_hits, sparse_hits, top_k)

    def vector_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self._dense_search(query_embedding, top_k, source_filter)

    def keyword_search(
        self,
        query_text: str,
        top_k: int = 10,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return self._keyword_search(query_text, top_k, source_filter)

    def _dense_search(
        self,
        query_embedding: List[float],
        top_k: int,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        filter_expr = None
        if source_filter:
            filter_expr = f'source like "%{source_filter}%"'

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
        return hits

    def _keyword_search(
        self,
        query_text: str,
        top_k: int,
        source_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        escaped = query_text.replace('"', '\\"')
        filter_parts = [f'text like "%{escaped}%"']
        if source_filter:
            filter_parts.append(f'source like "%{source_filter}%"')
        filter_expr = " and ".join(filter_parts)

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
            return {"exists": False, "num_entities": 0}
        stats = self.client.get_collection_stats(self.COLLECTION_NAME)
        return {"exists": True, "num_entities": stats.get("row_count", 0)}

    def find_by_hash(self, sha256_hash: str) -> Optional[str]:
        """Check if any entity has this SHA256 hash in metadata.
        Returns the source name if found, None otherwise."""
        if not sha256_hash:
            return None
        self._ensure_loaded()
        try:
            result = self.client.query(
                collection_name=self.COLLECTION_NAME,
                filter=f'metadata like "%{sha256_hash}%"',
                output_fields=["source", "metadata"],
                limit=1,
            )
            if result:
                meta = result[0].get("metadata", {})
                if isinstance(meta, dict) and meta.get("sha256") == sha256_hash:
                    return result[0].get("source")
            return None
        except Exception:
            return None

    def list_sources(self) -> List[Dict[str, Any]]:
        """List distinct sources with their chunk counts and latest metadata."""
        if not self.client.has_collection(self.COLLECTION_NAME):
            return []
        self._ensure_loaded()
        try:
            results = self.client.query(
                collection_name=self.COLLECTION_NAME,
                filter="id >= 0",
                output_fields=["source", "chunk_index", "metadata"],
                limit=10000,
            )
        except Exception:
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

        return sorted(sources.values(), key=lambda x: x["chunks"], reverse=True)

    def close(self):
        self._client = None
