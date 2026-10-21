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
    response = client.post("/register", data={"username": "student", "password": "haslo-testowe"})
    assert response.status_code == 400
    assert "zajeta" in response.text


def test_short_password_is_rejected(client):
    response = client.post("/register", data={"username": "nowy", "password": "krotkie"})
    assert response.status_code == 400
    assert "co najmniej" in response.text
