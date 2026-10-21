"""Dodaje dane demonstracyjne (konta i watki) do pustej bazy.

Lokalnie:      python -m scripts.seed_demo_data
W kontenerze:  docker compose exec app python -m scripts.seed_demo_data
"""

from argon2 import PasswordHasher
from sqlalchemy import select

from app.db import SessionLocal, init_db
from app.models import Post, Thread, User

DEMO_PASSWORD = "laboratorium"

THREADS = [
    (
        "anna",
        "Podzial zadan na laboratorium L2",
        [
            ("anna", "Proponuje: ja biore logowanie, Bartek forum, Celina docker compose."),
            ("bartek", "Pasuje. Dorzuce jeszcze walidacje formularzy."),
            ("celina", "Ok, przygotuje sprawozdanie i schemat architektury."),
        ],
    ),
    (
        "bartek",
        "Jaka baze wybieramy?",
        [
            ("bartek", "PostgreSQL w kontenerze, bo pozniej latwo przejdziemy na usluge w Azure."),
            ("anna", "Zgoda, lokalnie i tak wszystko stawiamy przez docker compose."),
        ],
    ),
]


def main() -> None:
    init_db()
    hasher = PasswordHasher()

    with SessionLocal() as db:
        if db.scalar(select(Thread)):
            print("Baza zawiera juz watki - pomijam.")
            return

        users = {}
        for name in ("anna", "bartek", "celina"):
            user = User(username=name, password_hash=hasher.hash(DEMO_PASSWORD))
            db.add(user)
            db.flush()
            users[name] = user

        for author, title, posts in THREADS:
            thread = Thread(title=title, author_id=users[author].id)
            db.add(thread)
            db.flush()
            for post_author, body in posts:
                db.add(Post(thread_id=thread.id, author_id=users[post_author].id, body=body))

        db.commit()

    print("Konta demo: anna, bartek, celina (haslo:", DEMO_PASSWORD + ")")


if __name__ == "__main__":
    main()
