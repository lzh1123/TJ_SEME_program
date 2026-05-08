from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pydantic import TypeAdapter

from ..domain.presentation import PresentationBundle


class PresentationRepository(Protocol):
    def save(self, bundle: PresentationBundle) -> None: ...

    def load(self, presentation_id: str) -> PresentationBundle: ...

    def exists(self, presentation_id: str) -> bool: ...


class FilePresentationRepository:
    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        self._adapter = TypeAdapter(PresentationBundle)

    def _dir(self, presentation_id: str) -> Path:
        return self._base_dir / "presentations" / presentation_id

    def exists(self, presentation_id: str) -> bool:
        return self._dir(presentation_id).exists()

    def save(self, bundle: PresentationBundle) -> None:
        pdir = self._dir(bundle.meta.id)
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / "bundle.json").write_text(
            json.dumps(bundle.model_dump(by_alias=True, mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self, presentation_id: str) -> PresentationBundle:
        pdir = self._dir(presentation_id)
        data = json.loads((pdir / "bundle.json").read_text(encoding="utf-8"))
        return self._adapter.validate_python(data)
