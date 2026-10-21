# Sprawozdanie L1 - Wybor aplikacji do implementacji

**Przedmiot:** Bezpieczenstwo serwerow i aplikacji Web, grupa 4
**Data laboratorium:** 2026-10-22

## 1. Wybrana aplikacja

**SecForum** - proste forum dyskusyjne. Zalogowany uzytkownik zaklada watki
i odpowiada w watkach innych osob; tresci czyta kazdy, pisze tylko osoba zalogowana.

Zakres celowo waski - trzy funkcje (konto, watek, odpowiedz). Rozbudowa UI nie wplywa
na ocene, a ciezar projektu lezy w kolejnych laboratoriach (architektura, CI/CD,
bezpieczenstwo, hardening, testy).

## 2. Realizacja wymagan L1

| Wymaganie | Realizacja |
| --- | --- |
| Prosta strona web z logowaniem (sesja) | rejestracja, logowanie, wylogowanie; sesja w podpisanym ciasteczku `HttpOnly` |
| Interakcja z uzytkownikiem (forum/chat/komentarze) | forum: lista watkow, zakladanie watku, odpowiedzi |
| Baza danych | PostgreSQL 16 w kontenerze (lokalnie mozna tez SQLite) |
| Technologia znana grupie | Python 3.12 + FastAPI + Jinja2 + SQLAlchemy |
| Srodowisko chmurowe | Azure + Azure DevOps (wdrozenie od L3/L4) |

## 3. Stos technologiczny

| Warstwa | Technologia | Dlaczego |
| --- | --- | --- |
| Backend | Python 3.12, FastAPI | jezyk znany grupie, malo kodu na prosty serwis |
| Widoki | Jinja2 (renderowanie po stronie serwera), CSS | brak budowania frontendu, mniej ruchomych czesci |
| Baza | SQLAlchemy + PostgreSQL 16 | standardowy ORM, baza latwa do przeniesienia do Azure |
| Hasla | Argon2 (`argon2-cffi`) | w bazie trzymamy wylacznie hasz hasla |
| Uruchomienie | Docker Compose (app + db) | jedno polecenie stawia cale srodowisko DEV |

## 4. Model danych

Trzy tabele:

- `users` - `id`, `username` (unikalny), `password_hash`, `created_at`
- `threads` - `id`, `title`, `author_id`, `created_at`
- `posts` - `id`, `thread_id`, `author_id`, `body`, `created_at`

Pierwszy wpis w watku powstaje razem z watkiem, kolejne to odpowiedzi.

## 5. Endpointy

| Metoda | Sciezka | Dostep | Opis |
| --- | --- | --- | --- |
| GET | `/` | publiczny | lista watkow |
| GET | `/threads/{id}` | publiczny | watek z wpisami |
| GET/POST | `/register` | publiczny | rejestracja |
| GET/POST | `/login` | publiczny | logowanie |
| POST | `/logout` | zalogowany | wylogowanie |
| GET/POST | `/threads/new` | zalogowany | nowy watek |
| POST | `/threads/{id}/posts` | zalogowany | odpowiedz w watku |
| GET | `/healthz` | infrastruktura | sprawdzenie, czy aplikacja zyje |

## 6. Stan na koniec L1

Aplikacja dziala lokalnie w Dockerze (`docker compose up`), ma dane demonstracyjne
i 10 testow pokrywajacych logowanie oraz obsluge watkow. Z rzeczy "bezpieczenstwowych"
sa tylko te wynikajace wprost z wymagania logowania: hasz hasla zamiast hasla jawnego
i sesja w ciasteczku `HttpOnly`. Reszta (naglowki, CSRF, WAF, monitoring, hardening)
jest swiadomie zostawiona na laboratoria L6-L8, zeby bylo widac roznice przed i po.

## 7. Uruchomienie

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec app python -m scripts.seed_demo_data
# http://localhost:43117, konta demo: anna / bartek / celina, haslo: laboratorium
```
