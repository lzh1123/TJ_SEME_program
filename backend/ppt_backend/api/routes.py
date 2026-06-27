from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from openai import APITimeoutError
from pydantic import BaseModel, Field

from ..domain.presentation import PresentationBundle
from ..domain.render_tree import ComponentPatch, RenderTree
from ..infrastructure.database import async_session_factory
from ..infrastructure.models import Presentation as PresentationModel
from ..services.presentation_service import PresentationService
from ..services.rag.task_queue import get_import_queue
from .deps import get_optional_current_user


router = APIRouter()


def get_service(req: Request) -> PresentationService:
    return req.app.state.presentation_service


def get_rag_service(req: Request):
    svc = req.app.state.presentation_service
    # _rag is None when RAG is disabled, so we don't need the type import at module level
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
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            None,
            lambda: svc.generate_outline(topic=payload.topic, theme=payload.theme, use_rag=payload.use_rag),
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
        raise HTTPException(status_code=504, detail="AI generation timed out — please try again.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/render-tree", response_model=RenderTree)
def compile_outline(payload: CompileOutlineRequest, svc: PresentationService = Depends(get_service)):
    try:
        bundle = svc.create_from_outline(topic=payload.topic, outline=payload.outline, theme=payload.theme)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return bundle.render_tree


@router.get("/presentations", response_model=List[dict])
async def list_presentations(
    svc: PresentationService = Depends(get_service),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    """List presentations. If authenticated, returns user's presentations only."""
    if current_user is None:
        return []

    # Support both dict (with "id" key) and string user_id
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user

    async with async_session_factory() as db:
        from sqlalchemy import select

        result = await db.execute(
            select(PresentationModel)
            .where(
                PresentationModel.user_id == user_id,
                PresentationModel.deleted_at.is_(None),
            )
            .order_by(PresentationModel.updated_at.desc())
        )
        rows = result.scalars().all()
        return [
            {
                "id": str(r.id),
                "title": r.title,
                "topic": r.topic,
                "theme": r.theme,
                "status": r.status,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
                "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]


@router.post("/presentations", response_model=CreatePresentationResponse)
async def create_presentation(
    payload: CreatePresentationRequest,
    request: Request,
    svc: PresentationService = Depends(get_service),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
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
        raise HTTPException(status_code=504, detail="AI generation timed out — please try again.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Link presentation to user in DB if authenticated
    if current_user:
        user_id = current_user["id"] if isinstance(current_user, dict) else current_user
        async with async_session_factory() as db:
            pres = PresentationModel(
                id=bundle.meta.id,
                user_id=user_id,
                title=bundle.meta.topic,
                topic=bundle.meta.topic,
                theme=bundle.dsl.theme if bundle.dsl else None,
                status="completed",
                bundle_path=str(
                    Path(svc._repo._base_dir) / "presentations" / bundle.meta.id / "bundle.json"
                ),
            )
            db.add(pres)
            await db.commit()

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
        raise HTTPException(status_code=504, detail="AI generation timed out — please try again.")
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
async def rag_upload_document(
    file: UploadFile = File(...),
    force: bool = False,
    svc: PresentationService = Depends(get_service),
):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        suffix = Path(file.filename or "upload").suffix or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        result = rag.ingest_document(
            Path(tmp_path),
            force=force,
            source_override=file.filename,
        )
        os.unlink(tmp_path)
        return {
            "filename": file.filename,
            "chunks_inserted": result.get("chunks_inserted", 0),
            "dedup_skipped": result.get("dedup_skipped", False),
            "action_taken": result.get("action_taken", "inserted"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rag/sources")
def rag_list_sources(svc: PresentationService = Depends(get_service)):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        return rag.list_sources()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rag/documents")
def rag_clear_all(svc: PresentationService = Depends(get_service)):
    """Clear all documents from the knowledge base."""
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        if hasattr(rag, "clear_all"):
            count = rag.clear_all()
            return {"message": "All documents cleared", "cleared": True, "chunks_removed": count}
        return {"message": "clear_all not supported", "cleared": False}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rag/documents/{source}")
def rag_remove_document(source: str, svc: PresentationService = Depends(get_service)):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    try:
        deleted = rag.remove_document(source)
        return {"source": source, "deleted": deleted}
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


# ── Eval endpoints ─────────────────────────────────────────────

@router.post("/eval/single/{presentation_id}")
def eval_single(
    presentation_id: str,
    payload: EvalSingleRequest,
    svc: PresentationService = Depends(get_service),
):
    from ..services.evaluation.evaluator import Evaluator

    try:
        bundle = svc.get(presentation_id)
        evaluator = Evaluator()
        result = evaluator.evaluate(
            presentation_bundle=bundle,
            reference_text=payload.reference_text,
            enable_llm_judge=payload.enable_llm_judge,
            metrics=payload.metrics,
        )
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Presentation not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/eval/batch")
def eval_batch(
    payload: BatchEvalRequestModel,
    svc: PresentationService = Depends(get_service),
):
    from ..services.evaluation.evaluator import Evaluator

    try:
        evaluator = Evaluator()
        results = []
        for config in payload.configs:
            for topic in payload.topics:
                try:
                    bundle = svc.create(topic=topic, theme=config.theme, use_rag=config.use_rag)
                    ref = payload.reference_texts.get(topic)
                    result = evaluator.evaluate(
                        presentation_bundle=bundle,
                        reference_text=ref,
                        metrics=payload.metrics,
                    )
                    result["config_name"] = config.name
                    result["topic"] = topic
                    results.append(result)
                except Exception as eval_err:
                    results.append({
                        "config_name": config.name,
                        "topic": topic,
                        "error": str(eval_err),
                    })
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Document import endpoints ─────────────────────────────────

class DocToOutlineRequest(BaseModel):
    model_config = {"extra": "forbid"}

    filename: str
    content: str


@router.post("/dsl/from-document")
async def dsl_from_document(
    payload: DocToOutlineRequest,
    request: Request,
    svc: PresentationService = Depends(get_service),
):
    """Generate an outline from document content (PDF/DOCX/TXT text)."""
    try:
        from ..services.rag.task_queue import process_document_to_outline

        result = await process_document_to_outline(
            content=payload.content,
            filename=payload.filename,
            svc=svc,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Task queue endpoints ──────────────────────────────────────

@router.get("/rag/tasks/{task_id}")
def get_task_status(task_id: str):
    queue = get_import_queue()
    task = queue.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
