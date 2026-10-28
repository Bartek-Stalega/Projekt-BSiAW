# Folium

Forum (projekt BSiAW, grupa 1). Watki czyta kazdy, pisze zalogowany uzytkownik.

Autorzy: Bartosz Stalga, Julia Aranowska, Dominik Baryla, Julek Jarzembowski.

- **Stos:** Python 3.12, FastAPI, Jinja2, SQLAlchemy, PostgreSQL 16, Docker Compose, Mailhog
- **Architektura:** [`docs/architektura.md`](docs/architektura.md)

## Uruchomienie (Docker)

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec app python -m scripts.seed_demo_data --force
```

- Aplikacja: http://localhost:43117
- Mailhog: http://localhost:8025
- Konta demo (haslo `laboratorium`): `admin`, `bartek`, `julek`, `julia`, `dominik`

Zatrzymanie: `docker compose down` (`-v` kasuje dane).

## Bez Dockera (SQLite)

```bash
make install
make run
```

## Funkcje

- rejestracja / logowanie (sesja HttpOnly, Argon2)
- watki i odpowiedzi, edytor WYSIWYG + obrazki
- admin (`/admin`), kasowanie tresci, blokada kont
- reset hasla e-mailem (Mailhog w DEV)

## Komendy

| Komenda | Opis |
| --- | --- |
| `make up` / `make down` | Docker start / stop |
| `make seed-force` | dane demo |
| `make test` | pytest |
| `make lint` | ruff |
