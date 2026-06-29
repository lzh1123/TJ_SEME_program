# Deferred imports: heavy dependencies (sentence-transformers, pymilvus) are loaded
# inside _build_rag_service() in container.py, not at module level.
# Import only lightweight utilities here.

from .rag_graph import build_rag_graph
from .seed_knowledge import SeedBootstrapper, SeedTopic, SEED_TOPICS
