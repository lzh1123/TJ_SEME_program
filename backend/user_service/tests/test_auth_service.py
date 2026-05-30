from datetime import datetime, timedelta, timezone

from app.core.config import Settings
from app.core.security import hash_password, transport_hash_password
from app.models.auth import (
    Permission,
    PolicyRule,
    RefreshToken,
    Role,
    RolePermission,
    ServiceCredential,
    UserRole,
    VerifyCode,
)
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.code_service import VerifyCodeService
from app.services.rbac_service import AuthorizationService


def make_settings():
    return Settings(
        AUTH_MODE="both",
        DATABASE_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/0",
        JWT_SECRET="test-secret",
        EMAIL_SMTP_ENABLED=False,
    )


def test_verify_code_send_and_check(db_session, fake_redis, monkeypatch):
    service = VerifyCodeService(db_session)
    monkeypatch.setattr(service.email_service, "send_verify_code", lambda **kwargs: None)
    monkeypatch.setattr(service, "_generate_code", lambda: "123456")

    service.send_code("user@example.com", "register")
    assert db_session.query(VerifyCode).count() == 1
    service.verify_code("user@example.com", "register", "123456", consume=True)
    record = db_session.query(VerifyCode).first()
    assert record.consumed_at is not None


def test_authorization_rbac_and_abac(db_session):
    user = User(email="u@example.com", username="u1", password_hash=hash_password("password123"))
    role = Role(name="admin")
    permission = Permission(code="user_profile:read")
    db_session.add_all([user, role, permission])
    db_session.commit()
    db_session.add_all(
        [
            UserRole(user_id=user.id, role_id=role.id),
            RolePermission(role_id=role.id, permission_id=permission.id),
        ]
    )
    db_session.commit()

    authorization = AuthorizationService(db_session)
    subject = authorization.build_subject(user)
    allowed, reason, matched = authorization.authorize(
        subject=subject,
        action="read",
        resource={"type": "user_profile", "id": user.id},
        context={"attributes": {}},
    )
    assert allowed is True
    assert reason
    assert matched == ["user_profile:read"]


def test_register_creates_user_and_tokens(db_session, fake_redis, monkeypatch):
    settings = make_settings()
    service = AuthService(db_session, fake_redis, settings)
    monkeypatch.setattr(service.code_service, "verify_code", lambda **kwargs: VerifyCode(
        id=1,
        target_type="email",
        target_value="a@b.com",
        purpose="register",
        code_hash="x",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        consumed_at=None,
        attempt_count=0,
    ))

    result = service.register(
        email="a@b.com",
        username="abc",
        password=transport_hash_password("password123"),
        verification_code="123456",
    )
    assert result.user.email == "a@b.com"
    assert result.auth.access_token is not None
    assert db_session.query(User).count() == 1
    assert db_session.query(RefreshToken).count() == 1


def test_policy_rule_authorization(db_session):
    user = User(email="p@example.com", username="policy-user", password_hash=hash_password("password123"))
    db_session.add(user)
    db_session.commit()
    db_session.add(
        PolicyRule(
            name="allow-internal-report-read",
            effect="allow",
            subject_kind="any",
            subject_values=[],
            action="read",
            resource_type="report",
            conditions={"is_internal": True},
        )
    )
    db_session.commit()

    authorization = AuthorizationService(db_session)
    subject = authorization.build_subject(user)
    allowed, reason, matched = authorization.authorize(
        subject=subject,
        action="read",
        resource={"type": "report", "id": "r-1"},
        context={"attributes": {"is_internal": True}},
    )
    assert allowed is True
    assert "policy rule" in reason
    assert matched == []


def test_verify_service_credential(db_session):
    db_session.add(
        ServiceCredential(
            service_name="gateway",
            token_hash=hash_password("service-secret"),
            active=True,
        )
    )
    db_session.commit()

    authorization = AuthorizationService(db_session)
    assert authorization.verify_service_credential("gateway", "service-secret") is True
    assert authorization.verify_service_credential("gateway", "wrong-secret") is False
