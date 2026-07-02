from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.test.sample_deck_fixtures import make_presentation_service
from backend.test.sample_deck_fixtures import sample_full_dsl


@pytest.fixture()
def client(tmp_path, monkeypatch):
    pytest.importorskip("jose")
    monkeypatch.setenv("RAG_ENABLED", "false")
    monkeypatch.setenv("PPT_DATA_DIR", str(tmp_path / "data"))

    from ppt_backend import settings as settings_module

    object.__setattr__(settings_module.settings, "rag_enabled", False)
    object.__setattr__(settings_module.settings, "data_dir", str(tmp_path / "data"))

    from ppt_backend.api.main import create_app

    app = create_app()
    app.state.presentation_service = make_presentation_service(tmp_path)
    return TestClient(app)


def test_runtime_health_themes_and_public_provider_endpoints(client):
    assert client.get("/health").json() == {"ok": True}

    themes = client.get("/themes")
    assert themes.status_code == 200
    assert isinstance(themes.json(), dict)
    assert "paper_light" in themes.json()

    providers = client.get("/llm/providers")
    assert providers.status_code == 200
    assert "providers" in providers.json()


def test_runtime_compile_outline_and_validation_errors(client):
    response = client.post(
        "/render-tree",
        json={
            "topic": "Runtime compile",
            "outline": sample_full_dsl(),
            "theme": "paper_light",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["themeName"] == "paper_light"
    assert len(data["slides"]) == len(sample_full_dsl()["slides"])

    invalid = client.post(
        "/render-tree",
        json={"topic": "bad", "outline": {}, "unexpected": True},
    )
    assert invalid.status_code == 422


def test_runtime_unauthenticated_and_missing_resource_behaviour(client):
    assert client.get("/presentations").status_code == 200
    assert client.get("/presentations").json() == []

    missing = client.get("/presentations/not-found")
    assert missing.status_code == 404

    rag = client.post(
        "/rag/search",
        json={"query": "software engineering", "top_k": 3, "enable_web": False, "enable_local": True},
    )
    assert rag.status_code == 503
