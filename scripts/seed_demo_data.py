"""Wypelnia baze danymi demonstracyjnymi (do prezentacji na laboratorium).

Uruchomienie lokalnie:        python -m scripts.seed_demo_data
Uruchomienie w kontenerze:    docker compose exec app python -m scripts.seed_demo_data

Skrypt jest idempotentny - przy ponownym uruchomieniu nic nie duplikuje.
"""

from sqlalchemy import func, select

from app.database import SessionLocal, init_db
from app.models import Post, Thread, User
from app.security import hash_password

DEMO_PASSWORD = "Laboratorium-2026"

DEMO_USERS = [
    ("anna", "anna@example.com"),
    ("bartek", "bartek@example.com"),
    ("celina", "celina@example.com"),
]

DEMO_THREADS = [
    (
        "anna",
        "Podzial zadan na laboratorium L2",
        [
            ("anna", "Proponuje: ja biore logowanie i sesje, Bartek forum, Celina docker compose."),
            ("bartek", "Pasuje. Dorzuce jeszcze walidacje formularzy i testy."),
            ("celina", "Ok, przygotuje tez sprawozdanie i schemat architektury."),
        ],
    ),
    (
        "bartek",
        "Czy sesje trzymamy w bazie czy w ciasteczku?",
        [
            (
                "bartek",
                "W ciasteczku bylby tylko podpisany token, ale wtedy trudno uniewaznic sesje.",
            ),
            (
                "anna",
                "Dlatego zrobilam sesje po stronie serwera - w ciasteczku jest losowy "
                "identyfikator, a w bazie jego skrot. Dzieki temu mozna wylogowac "
                "pojedyncze urzadzenie.",
            ),
        ],
    ),
    (
        "celina",
        "Pomysly na elementy bezpieczenstwa do L7",
        [
            (
                "celina",
                "Naglowki CSP i HSTS mamy juz w aplikacji, do tego WAF na warstwie brzegowej.",
            ),
            ("bartek", "Dodalbym jeszcze limit prob logowania i monitoring aktywnych sesji."),
        ],
    ),
]


def main() -> None:
    init_db()
    with SessionLocal() as db:
        if db.scalar(select(func.count(Thread.id))):
            print("Baza zawiera juz watki - pomijam seedowanie.")
            return

        users: dict[str, User] = {}
        for username, email in DEMO_USERS:
            user = db.scalar(select(User).where(User.username == username))
            if user is None:
                user = User(
                    username=username, email=email, password_hash=hash_password(DEMO_PASSWORD)
                )
                db.add(user)
                db.flush()
            users[username] = user

        for author, title, posts in DEMO_THREADS:
            thread = Thread(title=title, author_id=users[author].id)
            db.add(thread)
            db.flush()
            for post_author, body in posts:
                db.add(Post(thread_id=thread.id, author_id=users[post_author].id, body=body))

        db.commit()

    print("Dodano uzytkownikow demo:", ", ".join(name for name, _ in DEMO_USERS))
    print("Haslo dla kazdego konta:", DEMO_PASSWORD)


if __name__ == "__main__":
    main()
