from __future__ import annotations

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.database import async_session_factory
from ..services.auth_service import AuthService, decode_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async DB session with auto-commit/rollback."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db=db)


def _decode_user_id_from_token(token: str) -> Optional[str]:
    """Extract user_id from a JWT access token without DB query."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None
    return payload.get("sub")


async def get_optional_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[str]:
    """Return user_id string if a valid access token is provided, else None.
    No DB query is performed — the user is identified solely from the JWT claims.
    """
    if credentials is None:
        return None
    return _decode_user_id_from_token(credentials.credentials)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    """Require a valid access token and return user_id string.
    Raises 401 if token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = _decode_user_id_from_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return user_id


# Kept for backward compatibility with routes that expect dict-style user
async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[dict]:
    uid = await get_optional_current_user_id(credentials)
    if uid is None:
        return None
    return {"id": uid}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    uid = await get_current_user_id(credentials)
    return {"id": uid}
