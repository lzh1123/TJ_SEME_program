from dataclasses import dataclass
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import decode_token
from app.db.redis import get_redis
from app.db.session import get_db
from app.models.user import User
from app.services.rbac_service import AuthorizationService

bearer_scheme = HTTPBearer(auto_error=False)


DbSession = Annotated[Session, Depends(get_db)]
RedisClient = Annotated[Redis, Depends(get_redis)]
AppSettings = Annotated[Settings, Depends(get_settings)]


@dataclass
class AuthContext:
    user: User
    auth_type: str
    session_id: str | None = None
    token_payload: dict | None = None


def get_auth_context(
    db: DbSession,
    redis_client: RedisClient,
    settings: AppSettings,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session_header: Annotated[str | None, Header(alias="X-Session-Id")] = None,
    session_cookie: Annotated[str | None, Cookie(alias="session_id")] = None,
) -> AuthContext:
    if credentials:
        try:
            payload = decode_token(credentials.credentials)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject")

        session_id = payload.get("sid")
        user = db.get(User, int(user_id))
        if not user or user.status != "active":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")

        if settings.session_enabled and session_id:
            key = f"{settings.redis_session_prefix}:{session_id}"
            if not redis_client.exists(key):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

        return AuthContext(user=user, auth_type="jwt", session_id=session_id, token_payload=payload)

    session_id = session_header or session_cookie
    if settings.session_enabled and session_id:
        key = f"{settings.redis_session_prefix}:{session_id}"
        if not redis_client.exists(key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

        session_data = redis_client.hgetall(key)
        user_id = session_data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

        user = db.get(User, int(user_id))
        if not user or user.status != "active":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")

        return AuthContext(user=user, auth_type="session", session_id=session_id)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authentication")


def get_current_user(auth: Annotated[AuthContext, Depends(get_auth_context)]) -> User:
    return auth.user


def get_optional_auth_context(
    db: DbSession,
    redis_client: RedisClient,
    settings: AppSettings,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session_header: Annotated[str | None, Header(alias="X-Session-Id")] = None,
    session_cookie: Annotated[str | None, Cookie(alias="session_id")] = None,
) -> AuthContext | None:
    if not credentials and not session_header and not session_cookie:
        return None
    return get_auth_context(
        db=db,
        redis_client=redis_client,
        settings=settings,
        credentials=credentials,
        session_header=session_header,
        session_cookie=session_cookie,
    )


def require_internal_service(
    db: DbSession,
    settings: AppSettings,
    service_name: Annotated[str | None, Header(alias="X-Service-Name")] = None,
    service_token: Annotated[str | None, Header(alias="X-Service-Token")] = None,
) -> None:
    if service_token == settings.internal_service_token:
        return
    if not service_name or not service_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service credential")

    authorization = AuthorizationService(db)
    if not authorization.verify_service_credential(service_name, service_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service credential")
