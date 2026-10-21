from tests.conftest import register_and_login


def test_healthz_and_readyz(client):
    assert client.get("/healthz").json()["status"] == "ok"
    assert client.get("/readyz").json()["database"] == "ok"


def test_register_login_logout_flow(client):
    register_and_login(client)
    assert client.cookies.get("secforum_session") is not None

    page = client.get("/")
    assert "student" in page.text

    csrf = client.cookies.get("secforum_csrf")
    logout = client.post("/logout", data={"csrf_token": csrf}, follow_redirects=False)
    assert logout.status_code == 303
    assert client.cookies.get("secforum_session") is None


def test_login_with_wrong_password_is_generic(client):
    register_and_login(client)
    client.cookies.delete("secforum_session")

    csrf = client.cookies.get("secforum_csrf")
    response = client.post(
        "/login",
        data={"csrf_token": csrf, "username": "student", "password": "zle-haslo-123"},
    )
    assert response.status_code == 401
    assert "Nieprawidlowa nazwa uzytkownika lub haslo" in response.text


def test_login_without_csrf_token_is_rejected(client):
    response = client.post("/login", data={"username": "student", "password": "Haslo-Testowe-1"})
    assert response.status_code == 403


def test_weak_password_is_rejected(client):
    client.get("/register")
    csrf = client.cookies.get("secforum_csrf")
    response = client.post(
        "/register",
        data={
            "csrf_token": csrf,
            "username": "slaby",
            "email": "slaby@example.com",
            "password": "krotkie",
            "password_confirm": "krotkie",
        },
    )
    assert response.status_code == 400
    assert "co najmniej" in response.text


def test_account_lockout_after_failed_attempts(client):
    register_and_login(client)
    client.cookies.delete("secforum_session")

    for _ in range(5):
        csrf = client.cookies.get("secforum_csrf")
        client.post(
            "/login", data={"csrf_token": csrf, "username": "student", "password": "zle-haslo-123"}
        )

    csrf = client.cookies.get("secforum_csrf")
    response = client.post(
        "/login", data={"csrf_token": csrf, "username": "student", "password": "Haslo-Testowe-1"}
    )
    assert response.status_code == 401
    assert "zablokowane" in response.text


def test_session_cookie_is_httponly_and_opaque(client):
    register_and_login(client)
    cookie_header = "; ".join(
        value for key, value in client.cookies.items() if key == "secforum_session"
    )
    assert "student" not in cookie_header

    response = client.get("/")
    assert response.headers["content-security-policy"].startswith("default-src 'self'")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_sessions_page_requires_login(client):
    response = client.get("/account/sessions", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login?msg=login_required"


def test_user_can_list_and_revoke_sessions(client):
    register_and_login(client)
    page = client.get("/account/sessions")
    assert "ta sesja" in page.text

    csrf = client.cookies.get("secforum_csrf")
    response = client.post(
        "/account/sessions/revoke-others", data={"csrf_token": csrf}, follow_redirects=False
    )
    assert response.status_code == 303
