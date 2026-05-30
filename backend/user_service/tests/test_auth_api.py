from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db, get_redis, get_settings
from app.core.security import hash_password, transport_hash_password
from app.db.session import Base
from app.main import create_app
from app.models.auth import PolicyRule, ServiceCredential, VerifyCode
from app.models.user import User


def build_client(test_settings, fake_redis):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: fake_redis
    app.dependency_overrides[get_settings] = lambda: test_settings
    return app, TestClient(app), TestingSessionLocal


def test_register_login_and_me_flow(test_settings, fake_redis):
    app, client, SessionLocal = build_client(test_settings, fake_redis)
    with SessionLocal() as db:
        db.add(
            VerifyCode(
                target_type="email",
                target_value="user@example.com",
                purpose="register",
                code_hash=hash_password("123456"),
                expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
            )
        )
        db.commit()

    register_response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "username": "user1",
            "password": transport_hash_password("password123"),
            "verification_code": "123456",
        },
    )
    assert register_response.status_code == 200
    access_token = register_response.json()["auth"]["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "user@example.com"

    login_response = client.post(
        "/auth/login",
        json={"account": "user1", "password": transport_hash_password("password123")},
    )
    assert login_response.status_code == 200
    assert login_response.json()["auth"]["refresh_token"] is not None


def test_client_register_login_and_reset_password_flow(test_settings, fake_redis):
    app, client, SessionLocal = build_client(test_settings, fake_redis)
    with SessionLocal() as db:
        db.add(
            VerifyCode(
                target_type="email",
                target_value="client@example.com",
                purpose="register",
                code_hash=hash_password("123456"),
                expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
            )
        )
        db.add(
            VerifyCode(
                target_type="email",
                target_value="client@example.com",
                purpose="forgot_password",
                code_hash=hash_password("654321"),
                expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
            )
        )
        db.commit()

    register_response = client.post(
        "/auth/client-register",
        json={
            "email": "client@example.com",
            "username": "client-user",
            "password": "password123",
            "verification_code": "123456",
        },
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/client-login",
        json={"account": "client-user", "password": "password123"},
    )
    assert login_response.status_code == 200

    reset_response = client.post(
        "/auth/client-reset-password",
        json={
            "email": "client@example.com",
            "verification_code": "654321",
            "new_password": "new-password-123",
        },
    )
    assert reset_response.status_code == 200


def test_internal_introspect_and_authorize(test_settings, fake_redis):
    app, client, SessionLocal = build_client(test_settings, fake_redis)
    with SessionLocal() as db:
        user = User(
            email="svc@example.com",
            username="svc-user",
            password_hash=hash_password(transport_hash_password("password123")),
        )
        db.add(user)
        db.add(
            ServiceCredential(
                service_name="gateway",
                token_hash=hash_password("service-secret"),
                active=True,
            )
        )
        db.add(
            PolicyRule(
                name="allow-report-read-internal",
                effect="allow",
                subject_kind="any",
                subject_values=[],
                action="read",
                resource_type="report",
                conditions={"is_internal": True},
            )
        )
        db.commit()
        db.refresh(user)

    login_response = client.post(
        "/auth/login",
        json={"account": "svc-user", "password": transport_hash_password("password123")},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["auth"]["access_token"]

    introspect_response = client.post(
        "/auth/introspect",
        headers={"X-Service-Name": "gateway", "X-Service-Token": "service-secret"},
        json={"token": access_token},
    )
    assert introspect_response.status_code == 200
    assert introspect_response.json()["active"] is True

    authorize_response = client.post(
        "/auth/authorize",
        headers={"X-Service-Name": "gateway", "X-Service-Token": "service-secret"},
        json={
            "subject": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "status": user.status,
                "roles": [],
                "permissions": [],
            },
            "action": "read",
            "resource": {"type": "report", "id": "report-1", "attributes": {}},
            "context": {"attributes": {"is_internal": True}},
        },
    )
    assert authorize_response.status_code == 200
    assert authorize_response.json()["allowed"] is True
