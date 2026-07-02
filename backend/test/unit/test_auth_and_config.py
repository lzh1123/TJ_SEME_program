from __future__ import annotations

import pytest

from ppt_backend.services.presentation_service import resolve_page_count_target


def test_auth_tokens_and_password_helpers_when_dependencies_are_available():
    auth_service = pytest.importorskip("ppt_backend.services.auth_service")
    password_hash = auth_service.hash_password("correct horse battery staple")
    assert auth_service.verify_password("correct horse battery staple", password_hash)
    assert not auth_service.verify_password("wrong password", password_hash)

    access = auth_service.create_access_token("user-123")
    refresh = auth_service.create_refresh_token("user-123")
    assert auth_service.decode_token(access)["type"] == "access"
    assert auth_service.decode_token(refresh)["type"] == "refresh"
    assert auth_service.hash_token(refresh) == auth_service.hash_token(refresh)
    assert len(auth_service.hash_token(refresh)) == 64


def test_page_count_presets_resolve_to_generation_targets():
    assert resolve_page_count_target("short") == 9
    assert resolve_page_count_target("medium") == 14
    assert resolve_page_count_target("long") == 20
    assert resolve_page_count_target("unknown") == 14
