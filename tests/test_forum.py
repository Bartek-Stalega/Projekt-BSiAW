from tests.conftest import register_and_login


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

    assert "1 wpis" not in client.get("/").text  # watek + odpowiedz = 2 wpisy
    assert "2 wpisow" in client.get("/").text


def test_too_short_thread_is_rejected(client):
    register_and_login(client)
    response = client.post("/threads/new", data={"title": "a", "body": "b"})
    assert response.status_code == 400


def test_missing_thread_returns_404(client):
    response = client.get("/threads/999", headers={"accept": "text/html"})
    assert response.status_code == 404
    assert "Nie znaleziono watku" in response.text
