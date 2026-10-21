import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# Ustawienia musza byc gotowe przed importem aplikacji.
os.environ["APP_ENVIRONMENT"] = "test"
os.environ["APP_SECRET_KEY"] = "test-secret"
os.environ["APP_DATABASE_URL"] = f"sqlite:///{Path(tempfile.mkdtemp()) / 'test.db'}"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


def register_and_login(client: TestClient, username: str = "student") -> None:
    data = {"username": username, "password": "haslo-testowe"}
    assert client.post("/register", data=data, follow_redirects=False).status_code == 303
    assert client.post("/login", data=data, follow_redirects=False).status_code == 303
