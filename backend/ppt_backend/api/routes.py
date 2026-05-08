from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..domain.presentation import PresentationBundle
from ..domain.render_tree import ComponentPatch, RenderTree
from ..services.presentation_service import PresentationService


router = APIRouter()


def get_service(req: Request) -> PresentationService:
    return req.app.state.presentation_service


class CreatePresentationRequest(BaseModel):
    model_config = {"extra": "forbid"}

    topic: str
    theme: Optional[str] = None


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


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/themes")
def list_themes(svc: PresentationService = Depends(get_service)):
    return svc.list_themes()


@router.post("/presentations", response_model=CreatePresentationResponse)
def create_presentation(payload: CreatePresentationRequest, svc: PresentationService = Depends(get_service)):
    try:
        bundle = svc.create(topic=payload.topic, theme=payload.theme)
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
def regenerate(presentation_id: str, payload: RegenerateRequest, svc: PresentationService = Depends(get_service)):
    try:
        return svc.regenerate(presentation_id, topic=payload.topic, section=payload.section)
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

