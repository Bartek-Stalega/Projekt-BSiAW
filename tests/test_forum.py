from tests.conftest import register_and_login


def test_empty_forum_shows_placeholder(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Forum jest jeszcze puste" in response.text


def test_anonymous_user_cannot_create_thread(client):
    response = client.get("/threads/new", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login?msg=login_required"


def test_thread_and_reply_flow(client):
    register_and_login(client)

    csrf = client.cookies.get("secforum_csrf")
    response = client.post(
        "/threads/new",
        data={
            "csrf_token": csrf,
            "title": "Jak podzielic prace na L2?",
            "body": "Proponuje podzial na backend, frontend i infrastrukture.",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    thread_url = response.headers["location"].split("?")[0]

    reply = client.post(
        f"{thread_url}/posts",
        data={"csrf_token": csrf, "body": "Biore na siebie infrastrukture."},
        follow_redirects=False,
    )
    assert reply.status_code == 303

    page = client.get(thread_url)
    assert "Biore na siebie infrastrukture." in page.text
    assert "Jak podzielic prace na L2?" in page.text


def test_post_content_is_escaped(client):
    register_and_login(client)
    csrf = client.cookies.get("secforum_csrf")
    payload = "<script>alert('xss')</script>"
    response = client.post(
        "/threads/new",
        data={"csrf_token": csrf, "title": "Test XSS w tytule", "body": payload},
        follow_redirects=False,
    )
    thread_url = response.headers["location"].split("?")[0]

    page = client.get(thread_url)
    assert payload not in page.text
    assert "&lt;script&gt;" in page.text


def test_too_short_thread_is_rejected(client):
    register_and_login(client)
    csrf = client.cookies.get("secforum_csrf")
    response = client.post("/threads/new", data={"csrf_token": csrf, "title": "a", "body": "b"})
    assert response.status_code == 400


def test_missing_thread_returns_404_page(client):
    response = client.get("/threads/4242", headers={"accept": "text/html"})
    assert response.status_code == 404
    assert "Nie znaleziono watku" in response.text
