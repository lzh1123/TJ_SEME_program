from __future__ import annotations

import json

import pytest

from ppt_backend.repos.presentation_repo import FilePresentationRepository

from backend.test.sample_deck_fixtures import make_presentation_service


def test_file_presentation_repository_round_trips_bundle_json(tmp_path):
    service = make_presentation_service(tmp_path)
    bundle = service.create_from_outline(
        topic="Repository round trip",
        outline={
            "title": "Repository round trip",
            "slides": [{"intent": "cover", "title": "Repository", "subtitle": "Persistence"}],
        },
        theme="paper_light",
    )

    repo = FilePresentationRepository(tmp_path)
    bundle_path = tmp_path / "presentations" / bundle.meta.id / "bundle.json"

    assert repo.exists(bundle.meta.id)
    assert bundle_path.exists()
    saved = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert saved["meta"]["id"] == bundle.meta.id

    loaded = repo.load(bundle.meta.id)
    assert loaded.meta.id == bundle.meta.id
    assert loaded.dsl.title == "Repository round trip"
    assert len(loaded.render_tree.slides) == 1


def test_persistence_models_keep_required_table_contracts():
    pytest.importorskip("asyncpg")

    from ppt_backend.infrastructure.models.outline import Outline
    from ppt_backend.infrastructure.models.presentation import Presentation

    assert Outline.__tablename__ == "outlines"
    assert Presentation.__tablename__ == "presentations"

    outline_columns = set(Outline.__table__.columns.keys())
    presentation_columns = set(Presentation.__table__.columns.keys())

    assert {"id", "user_id", "title", "dsl", "slide_count", "created_at", "updated_at"} <= outline_columns
    assert {
        "id",
        "user_id",
        "title",
        "topic",
        "theme",
        "status",
        "bundle_path",
        "created_at",
        "updated_at",
        "deleted_at",
    } <= presentation_columns

    assert not Outline.__table__.columns["user_id"].nullable
    assert Presentation.__table__.columns["deleted_at"].nullable
