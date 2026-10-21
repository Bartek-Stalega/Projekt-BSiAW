# SecForum

Forum dyskusyjne grupy projektowej - projekt na laboratoria **Bezpieczenstwo serwerow
i aplikacji Web** (grupa 4). Zalogowany uzytkownik zaklada watki i odpowiada w watkach
innych osob; tresci czyta kazdy, pisze tylko uwierzytelniony uzytkownik.

Repozytorium realizuje etap **L1** (wybor aplikacji i implementacja), ale jest
zbudowane pod kolejne laboratoria: srodowisko lokalne w Dockerze odwzorowuje
docelowa architekture w **Azure**, a CI/CD opiera sie o **Azure DevOps**.

- Stos: Python 3.12, FastAPI, Jinja2 (SSR), SQLAlchemy 2.0, PostgreSQL 16, nginx, Docker
- Dokumentacja: [`docs/L1-sprawozdanie.md`](docs/L1-sprawozdanie.md),
  [`docs/architektura.md`](docs/architektura.md),
  [`docs/roadmap.md`](docs/roadmap.md),
  [`infra/azure/README.md`](infra/azure/README.md)

## Szybki start (Docker - srodowisko DEV)

```bash
cp .env.example .env            # ustaw wlasny APP_SECRET_KEY
docker compose up --build -d
docker compose exec app python -m scripts.seed_demo_data   # opcjonalnie: dane demo
```

Aplikacja: <http://localhost:43117> (port zmienisz zmienna `WEB_PORT`).
Konta demo: `anna`, `bartek`, `celina` - haslo `Laboratorium-2026`.

Zatrzymanie srodowiska: `docker compose down` (z `-v` kasuje takze dane bazy).

Test skalowania poziomego (sesje nie gina, bo leza w bazie):

```bash
docker compose up -d --scale app=3
```

## Uruchomienie bez Dockera (SQLite)

```bash
make install     # tworzy .venv i instaluje zaleznosci deweloperskie
make run         # http://127.0.0.1:43117 na bazie SQLite w ./data
```

## Komendy deweloperskie

| Komenda | Opis |
| --- | --- |
| `make test` | testy funkcjonalne i bezpieczenstwa (pytest) |
| `make lint` | analiza statyczna (ruff) |
| `make security` | Bandit (SAST) + pip-audit (podatnosci zaleznosci) |
| `make up` / `make down` | start / stop srodowiska Docker |
| `make logs` | logi aplikacji i reverse proxy |
| `make seed` | dane demonstracyjne w kontenerze |

## Konfiguracja

Wszystkie ustawienia pochodza ze zmiennych srodowiskowych z prefiksem `APP_`
(pelna lista w [`.env.example`](.env.example)). Najwazniejsze:

| Zmienna | Domyslnie | Opis |
| --- | --- | --- |
| `APP_ENVIRONMENT` | `local` | `local`/`dev` wlacza `/docs`; `prod` wylacza dokumentacje API |
| `APP_SECRET_KEY` | wartosc deweloperska | w chmurze z Azure Key Vault |
| `APP_DATABASE_URL` | SQLite w `./data` | w Dockerze i Azure: PostgreSQL |
| `APP_COOKIE_SECURE` | `false` | `true` po wpieciu TLS - wlacza `Secure` i HSTS |
| `APP_SESSION_IDLE_TIMEOUT_MINUTES` | `30` | limit bezczynnosci sesji |
| `APP_SESSION_ABSOLUTE_TTL_MINUTES` | `720` | bezwzgledny czas zycia sesji |

## Zabezpieczenia wdrozone na etapie L1

- Hasla: Argon2id, minimum 10 znakow, blokada konta po 5 nieudanych probach.
- Sesje serwerowe: w ciasteczku `HttpOnly`/`SameSite=Lax` tylko losowy token,
  w bazie jego SHA-256; limit bezczynnosci i bezwzgledny czas zycia; uzytkownik
  widzi swoje aktywne sesje i moze je uniewaznic (`/account/sessions`).
- CSRF: double-submit cookie na kazdym formularzu zmieniajacym stan.
- XSS: renderowanie po stronie serwera z autoescapingiem Jinja2 + waska polityka CSP.
- SQL injection: wylacznie zapytania parametryzowane przez SQLAlchemy.
- Naglowki: CSP, HSTS (przy TLS), `X-Frame-Options`, `X-Content-Type-Options`,
  `Referrer-Policy`, `Permissions-Policy`.
- Kontener: UID 10001 (non-root), `read_only`, `cap_drop: ALL`, `no-new-privileges`,
  baza w sieci `internal` bez portu na hoscie.
- Log audytowy zdarzen bezpieczenstwa + log dostepowy z naglowkiem `X-Request-ID`.

## Struktura repozytorium

```
app/            aplikacja (routery, modele, warstwa bezpieczenstwa, szablony, CSS)
infra/nginx/    reverse proxy dla srodowiska lokalnego
infra/azure/    projekt infrastruktury Azure (L3-L4)
pipelines/      pipeline Azure DevOps (L5-L6)
scripts/        skrypty pomocnicze (dane demo)
tests/          testy funkcjonalne i negatywne
docs/           sprawozdania i dokumentacja projektowa
```
