import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.auth import VerifyCode
from app.services.email_service import EmailService


class VerifyCodeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.email_service = EmailService()

    def _generate_code(self) -> str:
        return f"{secrets.randbelow(10**6):06d}"

    def _latest_code_query(self, email: str, purpose: str) -> Select[tuple[VerifyCode]]:
        return (
            select(VerifyCode)
            .where(
                VerifyCode.target_type == "email",
                VerifyCode.target_value == email,
                VerifyCode.purpose == purpose,
            )
            .order_by(desc(VerifyCode.id))
        )

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def send_code(self, email: str, purpose: str) -> None:
        latest = self.db.execute(self._latest_code_query(email, purpose)).scalars().first()
        now = datetime.now(timezone.utc)
        if latest and latest.created_at and (now - latest.created_at).total_seconds() < 60:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Code sent too frequently")

        code = self._generate_code()
        record = VerifyCode(
            target_type="email",
            target_value=email,
            purpose=purpose,
            code_hash=hash_password(code),
            expires_at=now + timedelta(minutes=10),
        )
        self.db.add(record)
        self.db.commit()
        self.email_service.send_verify_code(email=email, purpose=purpose, code=code)

    def verify_code(self, email: str, purpose: str, code: str, consume: bool = False) -> VerifyCode:
        record = self.db.execute(self._latest_code_query(email, purpose)).scalars().first()
        now = datetime.now(timezone.utc)
        if not record:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code not found")
        if record.consumed_at:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code already used")
        if self._normalize_datetime(record.expires_at) < now:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code expired")
        if not verify_password(code, record.code_hash):
            record.attempt_count += 1
            self.db.add(record)
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

        if consume:
            record.consumed_at = now
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)

        return record

    def fingerprint_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
