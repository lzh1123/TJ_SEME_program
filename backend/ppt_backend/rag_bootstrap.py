"""
一键知识库初始化 CLI

Usage:
    python -m ppt_backend.rag_bootstrap [--max-topics N] [--articles-per-topic N] [--reset]

Examples:
    python -m ppt_backend.rag_bootstrap                          # 完整初始化
    python -m ppt_backend.rag_bootstrap --max-topics 5            # 测试：只抓5个主题
    python -m ppt_backend.rag_bootstrap --articles-per-topic 5    # 每个主题抓5篇文章
    python -m ppt_backend.rag_bootstrap --reset                   # 清空后重新初始化
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(
        description="一键初始化 PPT 专业知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--max-topics", type=int, default=0, help="最多处理多少个主题 (0=全部)")
    parser.add_argument("--articles-per-topic", type=int, default=3, help="每个主题抓取的文章数")
    parser.add_argument("--reset", action="store_true", help="先清空已有知识库再初始化")
    args = parser.parse_args()

    from ppt_backend.settings import settings
    from ppt_backend.services.rag.embedding import EmbeddingService
    from ppt_backend.services.rag.milvus_client import MilvusStore
    from ppt_backend.services.rag.knowledge_base import KnowledgeBase
    from ppt_backend.services.rag.seed_knowledge import SeedBootstrapper, ContentFetcher

    print("=" * 60)
    print("  Slideon 专业知识库一键初始化")
    print("=" * 60)
    print(f"  Milvus URI:    {settings.milvus_uri}")
    print(f"  Embedding:     {settings.embedding_model}")
    print(f"  Max topics:    {'ALL' if args.max_topics == 0 else args.max_topics}")
    print(f"  Articles/topic: {args.articles_per_topic}")
    print(f"  Reset first:   {args.reset}")
    print()

    # 1. Connect to Milvus
    print("[1/4] Connecting to Milvus...")
    store = MilvusStore(uri=settings.milvus_uri, db_name=settings.milvus_db)
    if not store.available:
        print("  ERROR: Cannot connect to Milvus. Is Docker running?")
        print("  Run: cd backend/ppt_backend/milvus && ./standalone.bat start")
        return 1
    print("  Connected.")

    # 2. Load embedding model
    print("[2/4] Loading embedding model...")
    embedding = EmbeddingService(model_name=settings.embedding_model)
    print(f"  Model loaded. Dimension: {embedding.dim}")

    # 3. Ensure collection
    print("[3/4] Setting up knowledge base collection...")
    kb = KnowledgeBase(store=store, embedding=embedding)
    created = kb.ensure_collection(drop_if_exists=args.reset)
    print(f"  Collection {'created' if created else 'already exists'}.")

    # 4. Bootstrap
    print("[4/4] Starting knowledge bootstrapping...")
    print()

    bootstrapper = SeedBootstrapper(
        kb=kb,
        embedding=embedding,
        fetcher=ContentFetcher(),
        max_articles_per_topic=args.articles_per_topic,
        max_topics=args.max_topics,
    )

    def on_progress(prog):
        if prog.phase == "fetching" and prog.total > 0:
            pct = prog.topics_completed / prog.total * 100
            bar = "=" * int(pct / 5) + "-" * (20 - int(pct / 5))
            print(
                f"\r  [{bar}] {pct:.1f}% "
                f"({prog.topics_completed}/{prog.total} topics, "
                f"{prog.documents_ingested} docs, "
                f"{prog.chunks_ingested} chunks)",
                end="",
            )

    bootstrapper.on_progress(on_progress)
    t0 = time.time()
    result = bootstrapper.run()
    elapsed = time.time() - t0

    print()
    print()
    print("=" * 60)
    print("  Bootstrapping Complete!")
    print("=" * 60)
    print(f"  Topics processed:  {result.topics_completed}/{result.topics_total}")
    print(f"  Documents ingested: {result.documents_ingested}")
    print(f"  Chunks ingested:   {result.chunks_ingested}")
    print(f"  Errors:            {len(result.errors)}")
    print(f"  Time elapsed:      {elapsed:.1f}s")
    if result.errors:
        print()
        print("  Error details (first 5):")
        for e in result.errors[:5]:
            print(f"    - {e}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
