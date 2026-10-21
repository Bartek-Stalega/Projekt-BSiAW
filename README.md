# SecForum

Proste forum dyskusyjne - projekt na laboratoria **Bezpieczenstwo serwerow i aplikacji
Web** (grupa 4). Watki czyta kazdy, pisze tylko zalogowany uzytkownik.

To etap **L1**: wybor aplikacji i podstawowa implementacja. Elementy bezpieczenstwa
i infrastruktura chmurowa dochodza w kolejnych laboratoriach (patrz
[`docs/roadmap.md`](docs/roadmap.md)).

- **Stos:** Python 3.12, FastAPI, Jinja2, SQLAlchemy, PostgreSQL 16, Docker Compose
- **Docelowa chmura:** Azure + Azure DevOps (od L3)
- **Dokumentacja:** [sprawozdanie L1](docs/L1-sprawozdanie.md),
  [architektura](docs/architektura.md), [plan L1-L9](docs/roadmap.md)

## Uruchomienie w Dockerze

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec app python -m scripts.seed_demo_data   # opcjonalnie: dane demo
```

Aplikacja: <http://localhost:43117>
Konta demo: `anna`, `bartek`, `celina` - haslo `laboratorium`.

Zatrzymanie: `docker compose down` (z `-v` kasuje takze dane bazy).

## Uruchomienie bez Dockera (SQLite)

```bash
make install
make run      # http://127.0.0.1:43117
```

## Funkcje

- rejestracja i logowanie (sesja w podpisanym ciasteczku `HttpOnly`)
- lista watkow, zakladanie watku, odpowiedzi w watku
- dane w bazie PostgreSQL (lokalnie mozna tez na SQLite)

## Komendy

| Komenda | Opis |
| --- | --- |
| `make up` / `make down` | start / stop srodowiska Docker |
| `make logs` | logi aplikacji |
| `make seed` | dane demonstracyjne |
| `make test` | testy (pytest) |
| `make lint` | styl kodu (ruff) |

## Struktura

```
app/            aplikacja: modele, routery, szablony, style
scripts/        skrypt z danymi demo
tests/          testy
docs/           sprawozdanie i dokumentacja projektowa
infra/azure/    notatki o docelowej infrastrukturze (L3-L4)
pipelines/      szkielet pipeline'u Azure DevOps (L5)
```
