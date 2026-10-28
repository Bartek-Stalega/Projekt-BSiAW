import io

from tests.conftest import make_admin, register_and_login


def test_empty_forum_shows_placeholder(client):
    assert "Forum jest jeszcze puste" in client.get("/").text


def test_anonymous_user_is_redirected_to_login(client):
    response = client.get("/threads/new", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_thread_and_reply_flow(client):
    register_and_login(client)

    response = client.post(
        "/threads/new",
        data={"title": "Jak podzielic prace na L2?", "body": "Proponuje podzial na trzy czesci."},
        follow_redirects=False,
    )
    assert response.status_code == 303
    thread_url = response.headers["location"]

    client.post(thread_url + "/posts", data={"body": "Biore na siebie docker compose."})

    page = client.get(thread_url)
    assert "Jak podzielic prace na L2?" in page.text
    assert "Biore na siebie docker compose." in page.text

    index = client.get("/").text
    assert 'class="thread-replies">2</div>' in index
    assert 'class="thread-replies">1</div>' not in index


def test_too_short_thread_is_rejected(client):
    register_and_login(client)
    response = client.post("/threads/new", data={"title": "a", "body": "b"})
    assert response.status_code == 400


def test_missing_thread_returns_404(client):
    response = client.get("/threads/999", headers={"accept": "text/html"})
    assert response.status_code == 404
    assert "Nie znaleziono watku" in response.text


def test_markdown_bold_and_inline_image_upload(client):
    register_and_login(client)
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    upload = client.post(
        "/api/uploads",
        files={"image": ("bird.png", io.BytesIO(png), "image/png")},
    )
    assert upload.status_code == 200
    url = upload.json()["url"]
    assert url.startswith("/uploads/")

    body = f"Tekst przed.\n\n![dowod]({url})\n\nTekst **po** obrazku."
    response = client.post(
        "/threads/new",
        data={"title": "Obraz w srodku tresci", "body": body},
        follow_redirects=False,
    )
    assert response.status_code == 303
    page = client.get(response.headers["location"])
    assert url in page.text
    assert "<strong>po</strong>" in page.text
    assert "Tekst przed" in page.text


def test_admin_can_delete_thread(client):
    register_and_login(client, username="author")
    response = client.post(
        "/threads/new",
        data={"title": "Do skasowania przez admina", "body": "Tresc do usuniecia zaraz."},
        follow_redirects=False,
    )
    thread_url = response.headers["location"]
    client.post("/logout")

    register_and_login(client, username="admin")
    make_admin("admin")
    client.post("/logout")
    client.post("/login", data={"username": "admin", "password": "haslo-testowe"})

    delete = client.post(f"{thread_url}/delete", follow_redirects=False)
    assert delete.status_code == 303
    assert client.get(thread_url, headers={"accept": "text/html"}).status_code == 404


def test_non_admin_cannot_open_admin_panel(client):
    register_and_login(client)
    response = client.get("/admin", headers={"accept": "text/html"})
    assert response.status_code == 403
