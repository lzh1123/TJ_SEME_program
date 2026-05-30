from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def build_client(monkeypatch, **env):
    get_settings.cache_clear()
    for key, value in env.items():
        monkeypatch.setenv(key, str(value))
    app = create_app()
    return TestClient(app)


def test_force_https_redirect(monkeypatch):
    client = build_client(
        monkeypatch,
        FORCE_HTTPS="true",
        ALLOWED_HOSTS="testserver,localhost,127.0.0.1",
    )
    response = client.get("/health", follow_redirects=False, headers={"x-forwarded-proto": "http"})
    assert response.status_code == 307
    assert response.headers["location"].startswith("https://")


def test_hsts_header_on_https(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("HSTS_ENABLED", "true")
    monkeypatch.setenv("FORCE_HTTPS", "false")
    monkeypatch.setenv("ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
    client = TestClient(create_app(), base_url="https://testserver")
    response = client.get("/health")
    assert response.status_code == 200
    assert "strict-transport-security" in response.headers
