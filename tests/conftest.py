import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

# Ustawienia musza byc gotowe przed importem aplikacji.
_tmp = Path(tempfile.mkdtemp())
os.environ["APP_ENVIRONMENT"] = "test"
os.environ["APP_SECRET_KEY"] = "test-secret"
os.environ["APP_DATABASE_URL"] = f"sqlite:///{_tmp / 'test.db'}"
os.environ["APP_UPLOAD_DIR"] = str(_tmp / "uploads")
os.environ["APP_PUBLIC_BASE_URL"] = "http://testserver"
os.environ["APP_SMTP_HOST"] = "localhost"
os.environ["APP_SMTP_PORT"] = "1025"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client() -> Iterator[TestClient]:
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


def register_and_login(
    client: TestClient,
    username: str = "student",
    email: str | None = None,
    password: str = "haslo-testowe",
) -> None:
    data = {
        "username": username,
        "email": email or f"{username}@test.local",
        "password": password,
    }
    assert client.post("/register", data=data, follow_redirects=False).status_code == 303
    assert client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    ).status_code == 303


def make_admin(username: str = "admin") -> None:
    """Oznacza usera jako admina w bazie testowej."""
    from argon2 import PasswordHasher
    from sqlalchemy import select

    from app.db import SessionLocal
    from app.models import User

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            user = User(
                username=username,
                email=f"{username}@test.local",
                password_hash=PasswordHasher().hash("haslo-testowe"),
                is_admin=True,
            )
            db.add(user)
        else:
            user.is_admin = True
        db.commit()
