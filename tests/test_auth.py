from unittest.mock import patch

from tests.conftest import register_and_login


def test_healthz(client):
    assert client.get("/healthz").json()["status"] == "ok"


def test_register_login_logout(client):
    register_and_login(client)
    assert "student" in client.get("/").text

    assert client.post("/logout", follow_redirects=False).status_code == 303
    assert "Logowanie" in client.get("/").text


def test_login_with_wrong_password_fails(client):
    register_and_login(client)
    client.post("/logout")

    response = client.post("/login", data={"username": "student", "password": "inne-haslo"})
    assert response.status_code == 401
    assert "Nieprawidlowa nazwa uzytkownika lub haslo" in response.text


def test_duplicate_username_is_rejected(client):
    register_and_login(client)
    response = client.post(
        "/register",
        data={
            "username": "student",
            "email": "inny@test.local",
            "password": "haslo-testowe",
        },
    )
    assert response.status_code == 400
    assert "zajeta" in response.text


def test_short_password_is_rejected(client):
    response = client.post(
        "/register",
        data={"username": "nowy", "email": "nowy@test.local", "password": "krotkie"},
    )
    assert response.status_code == 400
    assert "co najmniej" in response.text


def test_password_reset_flow(client):
    register_and_login(client, username="resetme", email="resetme@test.local")
    client.post("/logout")

    with patch("app.routers.auth.send_password_reset") as mocked:
        resp = client.post(
            "/forgot-password",
            data={"email": "resetme@test.local"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        mocked.assert_called_once()
        raw_token = mocked.call_args.args[1]

    page = client.get(f"/reset-password?token={raw_token}")
    assert page.status_code == 200
    assert "Nowe haslo" in page.text or "nowe haslo" in page.text.lower()

    assert (
        client.post(
            "/reset-password",
            data={"token": raw_token, "password": "nowe-haslo-123"},
            follow_redirects=False,
        ).status_code
        == 303
    )

    assert (
        client.post(
            "/login",
            data={"username": "resetme", "password": "nowe-haslo-123"},
            follow_redirects=False,
        ).status_code
        == 303
    )
