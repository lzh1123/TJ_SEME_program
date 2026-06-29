from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..infrastructure.models import RefreshToken, User
from ..settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ───────────────────────────────────────


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT helpers ────────────────────────────────────────────


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload dict or None."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """Hash a refresh token for secure DB storage."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── Auth service ───────────────────────────────────────────


class AuthService:
    """Handles user registration, login, token management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Registration ──

    async def register(
        self,
        username: str,
        email: str,
        password: str,
        display_name: Optional[str] = None,
    ) -> User:
        """Register a new user. Raises ValueError on conflict."""
        # Check existing
        existing = await self.db.execute(
            select(User).where((User.username == username) | (User.email == email))
        )
        if existing.scalar_one_or_none():
            raise ValueError("Username or email already exists")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            display_name=display_name or username,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    # ── Login ──

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Verify credentials. Returns User or None."""
        result = await self.db.execute(
            select(User).where(
                (User.username == username) | (User.email == username)
            )
        )
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    async def create_tokens(
        self, user: User, device_info: Optional[str] = None, ip_address: Optional[str] = None
    ) -> dict:
        """Generate access + refresh tokens and persist the refresh token."""
        user_id_str = str(user.id)

        access_token = create_access_token(user_id_str)
        refresh_token = create_refresh_token(user_id_str)
        token_hash = hash_token(refresh_token)

        # Persist refresh token
        rt = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            device_info=device_info,
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(
                days=settings.jwt_refresh_token_expire_days
            ),
        )
        self.db.add(rt)

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    # ── Token refresh ──

    async def refresh_access_token(self, refresh_token: str) -> Optional[dict]:
        """Validate a refresh token and issue new token pair."""
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if user_id is None:
            return None

        # Verify it exists in DB and not revoked
        token_hash = hash_token(refresh_token)
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
        )
        stored = result.scalar_one_or_none()
        if stored is None:
            return None

        # Revoke old token (rotation)
        stored.revoked_at = datetime.now(timezone.utc)

        # Fetch user
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            return None

        return await self.create_tokens(user)

    # ── Get user by ID ──

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return None
        result = await self.db.execute(select(User).where(User.id == uid))
        return result.scalar_one_or_none()

    # ── Update profile ──

    async def update_profile(
        self,
        user_id: str,
        display_name: Optional[str] = None,
    ) -> Optional[User]:
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return None
        result = await self.db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            return None
        if display_name is not None:
            user.display_name = display_name
        await self.db.flush()
        return user

    # ── Logout (revoke all refresh tokens) ──

    async def logout(self, user_id: str) -> None:
        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            return
        await self.db.execute(
            RefreshToken.__table__.update()  # type: ignore[attr-defined]
            .where(
                RefreshToken.user_id == uid,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
