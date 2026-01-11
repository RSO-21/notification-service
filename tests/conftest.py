import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text


def _ensure_env():
    required = ["PGHOST", "PGUSER", "PGPASSWORD", "PGDATABASE"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            f"Missing env vars for tests: {missing}. "
            "In CI, set them via workflow env. Locally, export them or use a .env."
        )
    os.environ.setdefault("PGPORT", "5432")


@pytest.fixture(scope="session")
def app_and_engine():
    _ensure_env()

    from app.main import app
    from app.database import engine
    from app.models import Base

    schemas = ["public", "tenant1"]

    with engine.begin() as conn:
        for schema in schemas:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
            conn.execute(text(f'SET search_path TO "{schema}"'))
            Base.metadata.create_all(bind=conn)

    return app, engine


@pytest.fixture(autouse=True)
def _clean_db(app_and_engine):
    _, engine = app_and_engine
    schemas = ["public", "tenant1"]

    with engine.begin() as conn:
        for schema in schemas:
            conn.execute(text(f'SET search_path TO "{schema}"'))
            conn.execute(text("TRUNCATE TABLE notifications RESTART IDENTITY"))

    yield


@pytest.fixture()
def client(app_and_engine):
    app, _ = app_and_engine
    return TestClient(app)
