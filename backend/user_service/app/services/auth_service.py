import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from jose import JWTError
from redis import Redis
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models.auth import RefreshToken
from app.models.user import User
from app.schemas.auth import AuthResponse, TokenBundle
from app.schemas.common import UserSubject
from app.services.code_service import VerifyCodeService
from app.services.rbac_service import AuthorizationService


class AuthService:
    def __init__(self, db: Session, redis_client: Redis, settings: Settings) -> None:
        self.db = db
        self.redis = redis_client
        self.settings = settings
        self.code_service = VerifyCodeService(db)
        self.authorization_service = AuthorizationService(db)

    def _user_query(self, account: str):
        return select(User).where(or_(User.email == account, User.username == account))

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def _session_key(self, session_id: str) -> str:
        return f"{self.settings.redis_session_prefix}:{session_id}"

    def _create_session(self, user: User) -> str | None:
        if not self.settings.session_enabled:
            return None
        session_id = secrets.token_urlsafe(24)
        ttl_seconds = self.settings.session_ttl_days * 24 * 60 * 60
        self.redis.hset(
            self._session_key(session_id),
            mapping={"user_id": user.id, "status": user.status},
        )
        self.redis.expire(self._session_key(session_id), ttl_seconds)
        return session_id

    def _build_subject(self, user: User) -> UserSubject:
        return UserSubject.model_validate(self.authorization_service.build_subject(user))

    def _issue_tokens(self, user: User, session_id: str | None) -> TokenBundle:
        if not self.settings.jwt_enabled:
            return TokenBundle(session_id=session_id)

        access_ttl = timedelta(minutes=self.settings.jwt_access_ttl_minutes)
        refresh_ttl = timedelta(days=self.settings.jwt_refresh_ttl_days)
        refresh_jti = secrets.token_urlsafe(18)
        access_token = create_token(
            subject=str(user.id),
            token_type="access",
            expires_delta=access_ttl,
            extra={"sid": session_id, "username": user.username},
        )
        refresh_token = create_token(
            subject=str(user.id),
            token_type="refresh",
            expires_delta=refresh_ttl,
            extra={"sid": session_id, "jti": refresh_jti},
        )
        refresh_record = RefreshToken(
            user_id=user.id,
            session_id=session_id,
            token_jti=refresh_jti,
            token_hash=self._hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc) + refresh_ttl,
        )
        self.db.add(refresh_record)
        self.db.commit()

        return TokenBundle(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_ttl.total_seconds()),
            session_id=session_id,
        )

    def register(self, email: str, username: str, password: str, verification_code: str) -> AuthResponse:
        existing = self.db.execute(
            select(User).where(or_(User.email == email, User.username == username))
        ).scalars().first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

        self.code_service.verify_code(email=email, purpose="register", code=verification_code, consume=True)
        now = datetime.now(timezone.utc)
        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            status="active",
            email_verified_at=now,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        session_id = self._create_session(user)
        tokens = self._issue_tokens(user, session_id=session_id)
        return AuthResponse(user=self._build_subject(user), auth=tokens)

    def login(self, account: str, password: str) -> AuthResponse:
        user = self.db.execute(self._user_query(account)).scalars().first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if user.status != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

        session_id = self._create_session(user)
        tokens = self._issue_tokens(user, session_id=session_id)
        return AuthResponse(user=self._build_subject(user), auth=tokens)

    def refresh(self, refresh_token: str) -> TokenBundle:
        if not self.settings.jwt_enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JWT mode disabled")

        try:
            payload = decode_token(refresh_token)
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

        user_id = int(payload["sub"])
        token_jti = payload.get("jti")
        session_id = payload.get("sid")

        record = self.db.execute(
            select(RefreshToken).where(RefreshToken.token_jti == token_jti)
        ).scalars().first()
        if not record or record.revoked_at or record.token_hash != self._hash_token(refresh_token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
        if self._normalize_datetime(record.expires_at) < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
        if self.settings.session_enabled and session_id and not self.redis.exists(self._session_key(session_id)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

        user = self.db.get(User, user_id)
        if not user or user.status != "active":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")

        record.revoked_at = datetime.now(timezone.utc)
        self.db.add(record)
        self.db.commit()
        return self._issue_tokens(user, session_id=session_id)

    def refresh_session(self, user: User, session_id: str) -> TokenBundle:
        if not self.settings.session_enabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session mode disabled")

        key = self._session_key(session_id)
        if not self.redis.exists(key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

        ttl_seconds = self.settings.session_ttl_days * 24 * 60 * 60
        self.redis.expire(key, ttl_seconds)
        if self.settings.jwt_enabled:
            return self._issue_tokens(user, session_id=session_id)
        return TokenBundle(session_id=session_id)

    def logout(
        self,
        user: User,
        refresh_token: str | None = None,
        all_sessions: bool = False,
        current_session_id: str | None = None,
    ) -> None:
        if not self.settings.session_enabled:
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Logout is unavailable in JWT-only mode",
            )

        if all_sessions:
            pattern = f"{self.settings.redis_session_prefix}:*"
            for key in self.redis.scan_iter(pattern):
                payload = self.redis.hgetall(key)
                if str(payload.get("user_id")) == str(user.id):
                    self.redis.delete(key)

            records = self.db.execute(select(RefreshToken).where(RefreshToken.user_id == user.id)).scalars().all()
            now = datetime.now(timezone.utc)
            for record in records:
                record.revoked_at = now
                self.db.add(record)
            self.db.commit()
            return

        if refresh_token:
            try:
                payload = decode_token(refresh_token)
            except JWTError as exc:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

            token_jti = payload.get("jti")
            session_id = payload.get("sid")
            record = self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.token_jti == token_jti,
                    RefreshToken.user_id == user.id,
                )
            ).scalars().first()
            if record:
                record.revoked_at = datetime.now(timezone.utc)
                self.db.add(record)
                self.db.commit()
            if session_id:
                self.redis.delete(self._session_key(session_id))
            return

        if current_session_id:
            self.redis.delete(self._session_key(current_session_id))
            records = self.db.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == user.id,
                    RefreshToken.session_id == current_session_id,
                )
            ).scalars().all()
            now = datetime.now(timezone.utc)
            for record in records:
                record.revoked_at = now
                self.db.add(record)
            self.db.commit()

    def send_password_reset_code(self, email: str) -> None:
        user = self.db.execute(select(User).where(User.email == email)).scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        self.code_service.send_code(email=email, purpose="forgot_password")

    def reset_password(self, email: str, verification_code: str, new_password: str) -> None:
        user = self.db.execute(select(User).where(User.email == email)).scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        self.code_service.verify_code(
            email=email,
            purpose="forgot_password",
            code=verification_code,
            consume=True,
        )
        user.password_hash = hash_password(new_password)
        self.db.add(user)
        self.db.commit()
