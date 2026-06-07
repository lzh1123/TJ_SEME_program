from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from openai import APITimeoutError
from pydantic import BaseModel, Field

from ..domain.presentation import PresentationBundle
from ..domain.render_tree import ComponentPatch, RenderTree
from ..services.presentation_service import PresentationService
from ..services.rag.rag_service import RagService
from ..services.rag.task_queue import get_import_queue


router = APIRouter()


def get_service(req: Request) -> PresentationService:
    return req.app.state.presentation_service


def get_rag_service(req: Request):
    svc = req.app.state.presentation_service
    return getattr(svc, "_rag", None)


class CreatePresentationRequest(BaseModel):
    model_config = {"extra": "forbid"}

    topic: str
    theme: Optional[str] = None
    use_rag: bool = True


class CreatePresentationResponse(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    bundle: PresentationBundle


class ReorderSlidesRequest(BaseModel):
    model_config = {"extra": "forbid"}

    slide_ids: List[str] = Field(alias="slideIds")


class SwitchThemeRequest(BaseModel):
    model_config = {"extra": "forbid"}

    theme_name: str = Field(alias="themeName")
    rerender: bool = False


class RegenerateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    topic: Optional[str] = None
    section: Optional[str] = None
    use_rag: bool = True


class GenerateOutlineRequest(BaseModel):
    model_config = {"extra": "forbid"}

    topic: str
    theme: Optional[str] = None
    use_rag: bool = True


class CompileOutlineRequest(BaseModel):
    model_config = {"extra": "forbid"}

    topic: str
    outline: dict
    theme: Optional[str] = None


class RagSearchRequest(BaseModel):
    model_config = {"extra": "forbid"}

    query: str
    top_k: int = 5
    enable_web: bool = True
    enable_local: bool = True
    deep_fetch: bool = True


class EvalSingleRequest(BaseModel):
    model_config = {"extra": "forbid"}

    reference_text: Optional[str] = None
    enable_llm_judge: bool = True
    metrics: Optional[List[str]] = None


class BatchEvalConfigModel(BaseModel):
    name: str
    use_rag: bool = True
    theme: Optional[str] = None


class BatchEvalRequestModel(BaseModel):
    model_config = {"extra": "forbid"}

    configs: List[BatchEvalConfigModel]
    topics: List[str]
    metrics: Optional[List[str]] = None
    reference_texts: Dict[str, str] = Field(default_factory=dict)


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/themes")
def list_themes(svc: PresentationService = Depends(get_service)):
    return svc.list_themes()


@router.post("/dsl")
async def generate_outline(payload: GenerateOutlineRequest, request: Request, svc: PresentationService = Depends(get_service)):
    try:
        # Run blocking LLM work in thread pool so we can detect client disconnect
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            None,
            lambda: svc.generate_outline(topic=payload.topic, theme=payload.theme, use_rag=payload.use_rag),
        )
        # Poll until done or client disconnects
        while not future.done():
            if await request.is_disconnected():
                future.cancel()
                raise HTTPException(status_code=499, detail="Client disconnected")
            await asyncio.sleep(0.5)
        return future.result()
    except HTTPException:
        raise
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI generation timed out — the LLM service did not respond in time. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/render-tree", response_model=RenderTree)
def compile_outline(payload: CompileOutlineRequest, svc: PresentationService = Depends(get_service)):
    try:
        bundle = svc.create_from_outline(topic=payload.topic, outline=payload.outline, theme=payload.theme)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return bundle.render_tree


@router.post("/presentations", response_model=CreatePresentationResponse)
async def create_presentation(payload: CreatePresentationRequest, request: Request, svc: PresentationService = Depends(get_service)):
    try:
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            None,
            lambda: svc.create(topic=payload.topic, theme=payload.theme, use_rag=payload.use_rag),
        )
        while not future.done():
            if await request.is_disconnected():
                future.cancel()
                raise HTTPException(status_code=499, detail="Client disconnected")
            await asyncio.sleep(0.5)
        bundle = future.result()
    except HTTPException:
        raise
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI generation timed out — the LLM service did not respond in time. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return CreatePresentationResponse(id=bundle.meta.id, bundle=bundle)


@router.get("/presentations/{presentation_id}", response_model=PresentationBundle)
def get_presentation(presentation_id: str, svc: PresentationService = Depends(get_service)):
    try:
        return svc.get(presentation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/presentations/{presentation_id}/dsl")
def get_dsl(presentation_id: str, svc: PresentationService = Depends(get_service)):
    try:
        return svc.get(presentation_id).dsl
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not found")


@router.get("/presentations/{presentation_id}/render-tree", response_model=RenderTree)
def get_render_tree(presentation_id: str, svc: PresentationService = Depends(get_service)):
    try:
        return svc.get(presentation_id).render_tree
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not found")


@router.patch("/presentations/{presentation_id}/components/{component_id}", response_model=PresentationBundle)
def patch_component(
    presentation_id: str,
    component_id: str,
    patch: ComponentPatch = Body(...),
    svc: PresentationService = Depends(get_service),
):
    try:
        return svc.patch_component(presentation_id, component_id, patch)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not found")
    except KeyError:
        raise HTTPException(status_code=404, detail="component not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/presentations/{presentation_id}/slides/reorder", response_model=PresentationBundle)
def reorder_slides(presentation_id: str, payload: ReorderSlidesRequest, svc: PresentationService = Depends(get_service)):
    try:
        return svc.reorder_slides(presentation_id, payload.slide_ids)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/presentations/{presentation_id}/theme", response_model=PresentationBundle)
def switch_theme(presentation_id: str, payload: SwitchThemeRequest, svc: PresentationService = Depends(get_service)):
    try:
        return svc.switch_theme(presentation_id, payload.theme_name, rerender=payload.rerender)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/presentations/{presentation_id}/regenerate", response_model=PresentationBundle)
async def regenerate(presentation_id: str, payload: RegenerateRequest, request: Request, svc: PresentationService = Depends(get_service)):
    try:
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            None,
            lambda: svc.regenerate(presentation_id, topic=payload.topic, section=payload.section, use_rag=payload.use_rag),
        )
        while not future.done():
            if await request.is_disconnected():
                future.cancel()
                raise HTTPException(status_code=499, detail="Client disconnected")
            await asyncio.sleep(0.5)
        return future.result()
    except HTTPException:
        raise
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI generation timed out — the LLM service did not respond in time. Please try again.")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/presentations/{presentation_id}/export/pptx")
def export_pptx(presentation_id: str, svc: PresentationService = Depends(get_service)):
    try:
        out_path = svc.export_pptx(presentation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return FileResponse(
        path=str(out_path),
        filename=Path(out_path).name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


# ── RAG endpoints ──────────────────────────────────────────────

@router.post("/rag/search")
def rag_search(payload: RagSearchRequest, svc: PresentationService = Depends(get_service)):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        return rag.search(
            query=payload.query,
            top_k=payload.top_k,
            enable_web=payload.enable_web,
            enable_local=payload.enable_local,
            deep_fetch=payload.deep_fetch,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rag/documents")
def rag_upload_document(
    file: UploadFile = File(...),
    force: bool = False,
    svc: PresentationService = Depends(get_service),
):
    """Upload a single document to the knowledge base.

    Query params:
        force: If true, delete existing entries for this filename and re-ingest.
               If false (default), skip if the filename already exists (dedup).
    """
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        import tempfile
        import os

        suffix = Path(file.filename or "upload").suffix or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        result = rag.ingest_document(
            Path(tmp_path),
            force=force,
            source_override=file.filename,  # ← Use ORIGINAL filename, not temp name
        )
        os.unlink(tmp_path)
        return {
            "filename": file.filename,
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rag/documents")
def rag_clear_all_documents(svc: PresentationService = Depends(get_service)):
    """Delete ALL documents from the knowledge base. Use with caution."""
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        sources = rag.list_sources()
        total_deleted = 0
        for s in sources:
            source_name = s.get("source", "")
            if source_name:
                total_deleted += rag.remove_document(source_name)
        logging.getLogger(__name__).info(
            "KB clear: removed all %d sources, %d total chunks",
            len(sources), total_deleted,
        )
        return {
            "sources_removed": len(sources),
            "total_chunks_deleted": total_deleted,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rag/documents/{source}")
def rag_remove_document(source: str, svc: PresentationService = Depends(get_service)):
    """Delete a specific document from the knowledge base by source name."""
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        # Check if source exists before deleting
        count_before = rag.list_sources()
        matching = [s for s in count_before if s.get("source") == source]
        if not matching:
            all_names = [s.get("source", "") for s in count_before]
            return {
                "source": source,
                "deleted": 0,
                "warning": f"Source '{source}' not found in knowledge base.",
                "available_sources": all_names,
            }

        deleted = rag.remove_document(source)
        logging.getLogger(__name__).info(
            "KB delete: source=%r — %d chunks removed", source, deleted,
        )
        return {
            "source": source,
            "deleted": deleted,
            "chunks_before": matching[0].get("chunks", 0) if matching else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rag/stats")
def rag_stats(svc: PresentationService = Depends(get_service)):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        return rag.get_kb_stats()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rag/enhance")
def rag_enhance(payload: RagSearchRequest, svc: PresentationService = Depends(get_service)):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        context = rag.retrieve_context(
            query=payload.query,
            top_k=payload.top_k,
            enable_web=payload.enable_web,
            enable_local=payload.enable_local,
            deep_fetch=payload.deep_fetch,
        )
        return {"context": context}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rag/collection/init")
def rag_init_collection(svc: PresentationService = Depends(get_service)):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        created = rag.ensure_collection()
        stats = rag.get_kb_stats()
        return {"collection_created": created, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rag/collection/reset")
def rag_reset_collection(svc: PresentationService = Depends(get_service)):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        rag.ensure_collection(drop_if_exists=True)
        return {"message": "Collection reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class BootstrapRequest(BaseModel):
    model_config = {"extra": "forbid"}

    max_articles_per_topic: int = 3
    max_topics: int = 0


@router.post("/rag/bootstrap")
def rag_bootstrap(payload: BootstrapRequest, svc: PresentationService = Depends(get_service)):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        result = rag.bootstrap_knowledge_base(
            max_articles_per_topic=payload.max_articles_per_topic,
            max_topics=payload.max_topics,
        )
        return {
            "topics_completed": result.topics_completed,
            "topics_total": result.topics_total,
            "documents_ingested": result.documents_ingested,
            "chunks_ingested": result.chunks_ingested,
            "errors": len(result.errors),
            "error_details": result.errors[:10],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Document → Outline endpoint ─────────────────────────────────

@router.post("/dsl/from-document")
async def generate_outline_from_document(
    request: Request,
    file: UploadFile = File(...),
    theme: Optional[str] = Form(None),
    svc: PresentationService = Depends(get_service),
):
    """Upload a document (PDF/DOCX/TXT/MD), parse it, and generate an outline.

    NOTE: The document is NOT automatically added to the knowledge base.
    To add documents to KB, use POST /rag/documents or the KB management page."""
    try:
        suffix = Path(file.filename or "upload").suffix.lower()
        if suffix not in (".pdf", ".docx", ".txt", ".md"):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {suffix}. Supported: .pdf, .docx, .txt, .md",
            )

        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Parse document (reuse knowledge_base._read_file)
            from ..services.rag.knowledge_base import KnowledgeBase
            from ..services.rag.milvus_client import MilvusStore
            from ..services.rag.embedding import EmbeddingService
            from ..settings import settings

            store = MilvusStore(uri=settings.milvus_uri, db_name=settings.milvus_db)
            embedding = EmbeddingService(model_name=settings.embedding_model)
            kb = KnowledgeBase(store=store, embedding=embedding)
            doc_text = kb._read_file(Path(tmp_path), suffix)

            if not doc_text:
                raise HTTPException(status_code=400, detail="Could not extract text from document")

            # Truncate very long documents for the LLM prompt
            max_chars = 10000
            if len(doc_text) > max_chars:
                first = doc_text[:int(max_chars * 0.4)]
                last = doc_text[-int(max_chars * 0.2):]
                doc_text_for_llm = first + "\n\n...[content truncated]...\n\n" + last
            else:
                doc_text_for_llm = doc_text

            # Generate outline using document text as rag_context
            from ..services.ai.pipeline import AiPipeline
            ai = AiPipeline()
            dsl = ai.generate_dsl(
                topic=f"Based on document: {file.filename}",
                theme=theme,
                rag_context=doc_text_for_llm,
            )
            data = dsl.model_dump(by_alias=True)
            slides = data.get("slides") or []
            if isinstance(slides, list):
                for s in slides:
                    if isinstance(s, dict):
                        s.pop("id", None)
            data["slides"] = slides

            # NOTE: We intentionally do NOT auto-ingest the document into the
            # knowledge base here. KB is managed exclusively through the
            # /rag/documents endpoints. Users who want the document in KB
            # should explicitly upload it via the knowledge base page.

            return data

        finally:
            os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── KB Management endpoints ────────────────────────────────────

@router.post("/rag/documents/batch")
async def rag_upload_documents_batch(
    files: List[UploadFile] = File(...),
    svc: PresentationService = Depends(get_service),
):
    """Upload multiple documents for async KB import. Returns task_id."""
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")

    # Pair each temp file path with its original filename
    file_pairs: List[tuple] = []  # (temp_path, original_filename)
    for upload_file in files:
        original_name = upload_file.filename or "upload"
        file_suffix = Path(original_name).suffix or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp:
            tmp.write(await upload_file.read())
            file_pairs.append((Path(tmp.name), original_name))

    queue = get_import_queue()

    async def process_files(pairs: List[tuple], task: Any) -> None:
        skipped_count = 0
        for i, (temp_path, original_name) in enumerate(pairs):
            try:
                result = rag.ingest_document(
                    temp_path,
                    source_override=original_name,  # ← Use ORIGINAL filename
                )
                if result.get("dedup_skipped"):
                    skipped_count += 1
                    logging.getLogger(__name__).info(
                        "KB dedup: batch import skipped %s (already exists)", original_name
                    )
                task.processed = i + 1
            except Exception as e:
                task.errors.append(f"{original_name}: {type(e).__name__}: {e}")
            finally:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
        if skipped_count > 0:
            logging.getLogger(__name__).info(
                "KB dedup: batch import — %d/%d files skipped (already exist)",
                skipped_count, len(pairs),
            )

    queue.set_handler(process_files)
    task_id = queue.enqueue(file_pairs)

    return {"task_id": task_id, "file_count": len(files)}


@router.get("/rag/tasks/{task_id}")
def rag_task_status(task_id: str):
    """Get import task progress."""
    queue = get_import_queue()
    task = queue.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/rag/documents")
def rag_list_documents(svc: PresentationService = Depends(get_service)):
    """List all documents in the knowledge base with per-source chunk counts."""
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        stats = rag.get_kb_stats()
        sources = rag.list_sources()
        return {
            "exists": stats.get("exists", False),
            "num_entities": stats.get("num_entities", 0),
            "documents": sources,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Evaluation endpoints ───────────────────────────────────────

def _get_evaluator():
    """Lazy-load evaluator."""
    from ..services.evaluation.evaluator import Evaluator
    return Evaluator()


@router.post("/eval/single/{presentation_id}")
def eval_single_presentation(
    presentation_id: str,
    payload: EvalSingleRequest = Body(default=EvalSingleRequest()),
    svc: PresentationService = Depends(get_service),
):
    """Evaluate a single presentation's outline quality."""
    try:
        bundle = svc.get(presentation_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Presentation not found")

    slides_raw = bundle.dsl.model_dump(by_alias=True).get("slides", [])
    topic = bundle.meta.topic

    evaluator = _get_evaluator()
    result = evaluator.evaluate_single(
        presentation_id=presentation_id,
        topic=topic,
        slides=slides_raw,
        reference_text=payload.reference_text,
        enable_llm_judge=payload.enable_llm_judge,
        requested_metrics=payload.metrics,
    )
    return result.model_dump()


@router.post("/eval/batch")
async def eval_batch(
    payload: BatchEvalRequestModel,
    request: Request,
    svc: PresentationService = Depends(get_service),
):
    """Batch evaluate multiple configs × topics."""
    from ..services.evaluation.evaluator import Evaluator

    evaluator = Evaluator()
    results: List[dict] = []

    for config in payload.configs:
        for topic in payload.topics:
            try:
                loop = asyncio.get_event_loop()
                future = loop.run_in_executor(
                    None,
                    lambda t=topic, c=config: svc.create(
                        topic=t, theme=c.theme, use_rag=c.use_rag
                    ),
                )
                while not future.done():
                    if await request.is_disconnected():
                        future.cancel()
                        raise HTTPException(status_code=499, detail="Client disconnected")
                    await asyncio.sleep(0.5)
                bundle = future.result()

                slides_raw = bundle.dsl.model_dump(by_alias=True).get("slides", [])
                ref = payload.reference_texts.get(topic)

                eval_result = evaluator.evaluate_single(
                    presentation_id=bundle.meta.id,
                    topic=topic,
                    slides=slides_raw,
                    reference_text=ref,
                    enable_llm_judge="llm_judge" in (payload.metrics or []),
                    requested_metrics=payload.metrics,
                )
                result_dict = eval_result.model_dump()
                result_dict["config"] = config.name
                results.append(result_dict)
            except Exception as e:
                results.append({
                    "config": config.name,
                    "topic": topic,
                    "error": f"{type(e).__name__}: {e}",
                })

    return {
        "configs": [c.name for c in payload.configs],
        "topics": payload.topics,
        "results": results,
    }
