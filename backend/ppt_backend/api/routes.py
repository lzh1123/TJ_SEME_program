from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from openai import APITimeoutError
from pydantic import BaseModel, Field

from ..domain.presentation import PresentationBundle
from ..domain.render_tree import ComponentPatch, RenderTree
from ..infrastructure.database import async_session_factory
from ..infrastructure.models import Outline as OutlineModel
from ..infrastructure.models import Presentation as PresentationModel
from ..infrastructure.models import User as UserModel
from ..services.presentation_service import PresentationService
from ..services.ai.model_config import UserLLMConfig, list_public_providers
from ..services.rag.document_parser import (
    SUPPORTED_DOCUMENT_SUFFIXES,
    compact_document_text,
    parse_document,
)
from ..services.rag.task_queue import get_import_queue
from .deps import get_optional_current_user


router = APIRouter()


async def get_user_llm_config(current_user: Optional[dict]) -> UserLLMConfig:
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录并在个人资料页配置大模型")
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    try:
        uid = uuid.UUID(str(user_id))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user")
    from sqlalchemy import select
    async with async_session_factory() as db:
        result = await db.execute(select(UserModel).where(UserModel.id == uid))
        user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.llm_provider or not user.llm_api_key:
        raise HTTPException(status_code=400, detail="请先在个人资料页配置大模型和 API Key")
    return UserLLMConfig(
        provider=user.llm_provider,
        model=user.llm_model,
        api_base=user.llm_api_base,
        api_key=user.llm_api_key,
    )


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
    model_config = {"extra": "forbid", "populate_by_name": True}

    topic: str
    theme: Optional[str] = None
    use_rag: bool = True
    model_provider: str = Field("deepseek", alias="modelProvider")
    page_count_preset: str = Field("medium", alias="pageCountPreset")


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


@router.get("/llm/providers")
def list_llm_providers():
    return {"providers": list_public_providers()}


@router.get("/themes")
def list_themes(svc: PresentationService = Depends(get_service)):
    return svc.list_themes()


@router.post("/dsl")
async def generate_outline(
    payload: GenerateOutlineRequest,
    request: Request,
    svc: PresentationService = Depends(get_service),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    try:
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            None,
            lambda: svc.generate_outline(
                topic=payload.topic,
                theme=payload.theme,
                use_rag=payload.use_rag,
                model_provider=payload.model_provider,
                page_count_preset=payload.page_count_preset,
            ),
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
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录再上传文档")
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    try:
        suffix = Path(file.filename or "upload").suffix or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        result = rag.ingest_document(
            Path(tmp_path),
            force=force,
            source_override=file.filename,
            user_id=user_id,
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


@router.post("/rag/documents/batch")
async def rag_upload_documents_batch(
    files: List[UploadFile] = File(...),
    force: bool = False,
    svc: PresentationService = Depends(get_service),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    """Upload multiple documents for async KB import. Returns task_id."""
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    if not current_user:
        raise HTTPException(status_code=401, detail="Please log in before uploading documents")
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user

    file_pairs: List[tuple[Path, str]] = []
    try:
        for upload_file in files:
            original_name = upload_file.filename or "upload"
            file_suffix = Path(original_name).suffix or ".txt"
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix) as tmp:
                tmp.write(await upload_file.read())
                file_pairs.append((Path(tmp.name), original_name))
    except Exception:
        for temp_path, _ in file_pairs:
            try:
                os.unlink(temp_path)
            except Exception:
                pass
        raise

    queue = get_import_queue()

    async def process_files(pairs: List[tuple[Path, str]], task: Any) -> None:
        skipped_count = 0
        for i, (temp_path, original_name) in enumerate(pairs):
            try:
                result = rag.ingest_document(
                    temp_path,
                    force=force,
                    source_override=original_name,
                    user_id=user_id,
                )
                if result.get("dedup_skipped"):
                    skipped_count += 1
                task.processed = i + 1
            except Exception as e:
                task.errors.append(f"{original_name}: {type(e).__name__}: {e}")
            finally:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
        if skipped_count:
            logging.getLogger(__name__).info(
                "KB batch import skipped %d/%d duplicate files for user=%s",
                skipped_count,
                len(pairs),
                user_id,
            )

    task_id = queue.enqueue(file_pairs, handler=process_files)

    return {"task_id": task_id, "file_count": len(files)}


@router.get("/rag/sources")
def rag_list_sources(
    svc: PresentationService = Depends(get_service),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    if not current_user:
        return []
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    try:
        return rag.list_sources(user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rag/documents")
def rag_list_documents(
    svc: PresentationService = Depends(get_service),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    """List documents in the current user's knowledge base with chunk counts."""
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    if not current_user:
        return {"exists": True, "num_entities": 0, "documents": []}
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    try:
        sources = rag.list_sources(user_id=user_id)
        actual_entities = sum(s.get("chunks", 0) for s in sources)
        return {
            "exists": True,
            "num_entities": actual_entities,
            "documents": sources,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rag/documents")
def rag_clear_all(
    svc: PresentationService = Depends(get_service),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    """Clear all current-user documents from the knowledge base."""
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    if not current_user:
        raise HTTPException(status_code=401, detail="Please log in before clearing documents")
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    try:
        sources = rag.list_sources(user_id=user_id)
        total_deleted = 0
        for source in sources:
            source_name = source.get("source", "")
            if source_name:
                total_deleted += rag.remove_document(source_name, user_id=user_id)
        return {
            "sources_removed": len(sources),
            "total_chunks_deleted": total_deleted,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rag/documents/{source}")
def rag_remove_document(
    source: str,
    svc: PresentationService = Depends(get_service),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    if not current_user:
        raise HTTPException(status_code=401, detail="请先登录")
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    try:
        # Verify the source belongs to the current user
        sources = rag.list_sources(user_id=user_id)
        if not any(s.get("source") == source for s in sources):
            raise HTTPException(status_code=404, detail="Source not found or not owned by you")
        deleted = rag.remove_document(source, user_id=user_id)
        return {"source": source, "deleted": deleted}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rag/documents/{source}/preview")
def rag_preview_document(
    source: str,
    max_chunks: int = 20,
    svc: PresentationService = Depends(get_service),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    rag = getattr(svc, "_rag", None)
    if not rag:
        raise HTTPException(status_code=503, detail="RAG service not available")
    if not current_user:
        raise HTTPException(status_code=401, detail="Please log in before previewing documents")
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    try:
        preview = rag.preview_document(source, user_id=user_id, max_chunks=max(1, min(max_chunks, 50)))
        if not preview.get("preview_text"):
            raise HTTPException(status_code=404, detail="Document not found")
        return preview
    except HTTPException:
        raise
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
    model_config = {"extra": "forbid", "populate_by_name": True}

    filename: str
    content: str
    model_provider: str = Field("deepseek", alias="modelProvider")
    page_count_preset: str = Field("medium", alias="pageCountPreset")


@router.post("/dsl/from-document")
async def dsl_from_document(
    request: Request,
    svc: PresentationService = Depends(get_service),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    """Generate an outline from uploaded document file or extracted document text."""
    tmp_path: Optional[str] = None
    try:
        content_type = request.headers.get("content-type", "")
        theme: Optional[str] = None
        model_provider = "deepseek"
        page_count_preset = "medium"

        if content_type.startswith("multipart/form-data"):
            form = await request.form()
            upload = form.get("file")
            if upload is None or not hasattr(upload, "read"):
                raise HTTPException(status_code=400, detail="File is required")
            filename = upload.filename or "upload"
            suffix = Path(filename).suffix.lower()
            if suffix not in SUPPORTED_DOCUMENT_SUFFIXES:
                supported = ", ".join(sorted(SUPPORTED_DOCUMENT_SUFFIXES))
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {suffix or '(none)'}. Supported: {supported}",
                )
            theme_value = form.get("theme")
            theme = str(theme_value) if theme_value else None
            provider_value = form.get("modelProvider") or form.get("model_provider")
            model_provider = str(provider_value) if provider_value else "deepseek"
            preset_value = form.get("pageCountPreset") or form.get("page_count_preset")
            page_count_preset = str(preset_value) if preset_value else "medium"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await upload.read())
                tmp_path = tmp.name
            content = parse_document(Path(tmp_path), suffix)
        else:
            payload = DocToOutlineRequest.model_validate(await request.json())
            filename = payload.filename
            content = payload.content
            model_provider = payload.model_provider
            page_count_preset = payload.page_count_preset

        content = content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="Could not extract text from document")

        from ..services.ai.pipeline import AiPipeline

        ai = AiPipeline(model_provider=model_provider)
        dsl = ai.generate_dsl(
            topic=f"基于上传文档生成大纲：{filename}",
            theme=theme,
            rag_context=compact_document_text(content),
            target_slide_count=9 if page_count_preset == "short" else 20 if page_count_preset == "long" else 14,
            page_count_preset=page_count_preset,
        )
        data = dsl.model_dump(by_alias=True)
        data.pop("theme", None)
        slides = data.get("slides") or []
        if isinstance(slides, list):
            for slide in slides:
                if isinstance(slide, dict):
                    slide.pop("id", None)
        data["slides"] = slides
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ── Task queue endpoints ──────────────────────────────────────

@router.get("/rag/tasks/{task_id}")
def get_task_status(task_id: str):
    queue = get_import_queue()
    task = queue.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ── Outline endpoints (cloud sync for logged-in users) ─────────

class OutlineCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    id: str
    title: str = Field(..., max_length=500)
    dsl: str
    slide_count: int = 0


class OutlineUpdateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    title: Optional[str] = Field(None, max_length=500)
    dsl: Optional[str] = None
    slide_count: Optional[int] = None


@router.get("/outlines")
async def list_outlines(
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    if not current_user:
        return []
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    async with async_session_factory() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(OutlineModel)
            .where(OutlineModel.user_id == user_id)
            .order_by(OutlineModel.updated_at.desc())
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "slideCount": r.slide_count,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
                "updatedAt": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]


@router.post("/outlines")
async def create_outline(
    payload: OutlineCreateRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    async with async_session_factory() as db:
        outline = OutlineModel(
            id=payload.id,
            user_id=user_id,
            title=payload.title,
            dsl=payload.dsl,
            slide_count=payload.slide_count,
        )
        db.add(outline)
        await db.commit()
        await db.refresh(outline)
        return {
            "id": outline.id,
            "title": outline.title,
            "slideCount": outline.slide_count,
            "createdAt": outline.created_at.isoformat() if outline.created_at else None,
            "updatedAt": outline.updated_at.isoformat() if outline.updated_at else None,
        }


@router.get("/outlines/{outline_id}")
async def get_outline(
    outline_id: str,
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    async with async_session_factory() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(OutlineModel).where(
                OutlineModel.id == outline_id,
                OutlineModel.user_id == user_id,
            )
        )
        outline = result.scalar_one_or_none()
        if outline is None:
            raise HTTPException(status_code=404, detail="Outline not found")
        return {
            "id": outline.id,
            "title": outline.title,
            "dsl": outline.dsl,
            "slideCount": outline.slide_count,
            "createdAt": outline.created_at.isoformat() if outline.created_at else None,
            "updatedAt": outline.updated_at.isoformat() if outline.updated_at else None,
        }


@router.put("/outlines/{outline_id}")
async def update_outline(
    outline_id: str,
    payload: OutlineUpdateRequest,
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    from datetime import datetime, timezone
    from sqlalchemy import text
    now = datetime.now(timezone.utc)
    sets = ["updated_at = :now"]
    params = {"oid": outline_id, "uid": user_id, "now": now}
    if payload.title is not None:
        sets.append("title = :title")
        params["title"] = payload.title
    if payload.dsl is not None:
        sets.append("dsl = :dsl")
        params["dsl"] = payload.dsl
    if payload.slide_count is not None:
        sets.append("slide_count = :sc")
        params["sc"] = payload.slide_count
    async with async_session_factory() as db:
        update_result = await db.execute(
            text(f"UPDATE outlines SET {', '.join(sets)} WHERE id = :oid AND user_id = :uid"),
            params
        )
        if update_result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Outline not found")
        await db.commit()
        # Fetch updated record
        from sqlalchemy import select
        result = await db.execute(
            select(OutlineModel).where(
                OutlineModel.id == outline_id,
                OutlineModel.user_id == user_id,
            )
        )
        outline = result.scalar_one_or_none()
        if outline is None:
            raise HTTPException(status_code=404, detail="Outline not found")
        return {
            "id": outline.id,
            "title": outline.title,
            "slideCount": outline.slide_count,
            "createdAt": outline.created_at.isoformat() if outline.created_at else None,
            "updatedAt": outline.updated_at.isoformat() if outline.updated_at else None,
        }


@router.delete("/outlines/{outline_id}")
async def delete_outline(
    outline_id: str,
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    from sqlalchemy import select
    async with async_session_factory() as db:
        result = await db.execute(
            select(OutlineModel).where(
                OutlineModel.id == outline_id,
                OutlineModel.user_id == user_id,
            )
        )
        outline = result.scalar_one_or_none()
        if outline is None:
            raise HTTPException(status_code=404, detail="Outline not found")
        await db.delete(outline)
        await db.commit()
        return {"message": "Deleted"}
