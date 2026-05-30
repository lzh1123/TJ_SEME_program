import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.session import Base
from app.models import auth as _auth_models  # noqa: F401
from app.models import user as _user_models  # noqa: F401


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class FakeRedis:
    def __init__(self):
        self.store = {}
        self.expiries = {}

    def hset(self, key, mapping):
        self.store[key] = dict(mapping)

    def expire(self, key, ttl):
        self.expiries[key] = ttl

    def exists(self, key):
        return 1 if key in self.store else 0

    def hgetall(self, key):
        return self.store.get(key, {})

    def delete(self, key):
        self.store.pop(key, None)

    def scan_iter(self, pattern):
        prefix = pattern.rstrip("*")
        for key in list(self.store.keys()):
            if key.startswith(prefix):
                yield key


@pytest.fixture()
def fake_redis():
    return FakeRedis()


@pytest.fixture()
def test_settings():
    return Settings(
        AUTH_MODE="both",
        DATABASE_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/0",
        JWT_SECRET="test-secret",
        EMAIL_SMTP_ENABLED=False,
        INTERNAL_SERVICE_TOKEN="internal-token",
        ALLOWED_HOSTS="testserver,localhost,127.0.0.1",
    )
