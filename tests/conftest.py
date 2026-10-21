import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# Konfiguracja testowa musi byc ustawiona przed importem aplikacji,
# bo ustawienia sa czytane raz i cache'owane.
_tmp_dir = tempfile.mkdtemp(prefix="secforum-tests-")
os.environ["APP_ENVIRONMENT"] = "test"
os.environ["APP_SECRET_KEY"] = "test-secret-key"
os.environ["APP_DATABASE_URL"] = f"sqlite:///{Path(_tmp_dir) / 'test.db'}"
os.environ["APP_COOKIE_SECURE"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


def register_and_login(
    client: TestClient, username: str = "student", password: str = "Haslo-Testowe-1"
) -> None:
    client.get("/register")
    csrf = client.cookies.get("secforum_csrf")
    response = client.post(
        "/register",
        data={
            "csrf_token": csrf,
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
            "password_confirm": password,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text

    csrf = client.cookies.get("secforum_csrf")
    response = client.post(
        "/login",
        data={"csrf_token": csrf, "username": username, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text
