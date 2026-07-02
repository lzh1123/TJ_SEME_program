from __future__ import annotations

import uuid
import asyncio
from types import SimpleNamespace


def test_update_profile_route_returns_updated_user_response():
    from ppt_backend.api.auth_routes import UpdateProfileRequest, update_me

    user_id = str(uuid.uuid4())

    class FakeAuthService:
        async def update_profile(self, user_id: str, display_name: str | None = None):
            return SimpleNamespace(
                id=uuid.UUID(user_id),
                username="route_user",
                email="route_user@example.test",
                display_name=display_name,
                last_login_at=None,
                is_active=True,
            )

    response = asyncio.run(
        update_me(
            payload=UpdateProfileRequest(displayName="Updated Name"),
            current_user_id=user_id,
            auth=FakeAuthService(),
        )
    )

    assert response.username == "route_user"
    assert response.display_name == "Updated Name"
