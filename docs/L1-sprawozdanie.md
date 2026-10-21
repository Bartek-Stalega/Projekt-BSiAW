# Sprawozdanie L1 - Wybor aplikacji do implementacji

**Przedmiot:** Bezpieczenstwo serwerow i aplikacji Web - laboratoria, grupa 4
**Data laboratorium:** 2026-10-22
**Temat:** L1. Wybor aplikacji i implementacja

## 1. Wybrana aplikacja

**SecForum** - proste forum dyskusyjne grupy projektowej. Zalogowany uzytkownik
zaklada watki i odpowiada w watkach zalozonych przez innych; tresci sa widoczne
publicznie, ale pisac moga tylko uwierzytelnieni uzytkownicy.

Zakres swiadomie ograniczony do jednej, kompletnej funkcjonalnosci - ciezar
projektu lezy w warstwie bezpieczenstwa i infrastruktury, a nie w rozbudowie UI.

## 2. Realizacja wymagan funkcjonalnych L1

| Wymaganie | Realizacja |
| --- | --- |
| Prosta strona web z logowaniem (sesja) | Rejestracja, logowanie, wylogowanie; sesja serwerowa w bazie, w ciasteczku `HttpOnly` wylacznie losowy token |
| Interakcja z uzytkownikiem (forum/chat/komentarze) | Forum: lista watkow, zakladanie watku, odpowiedzi w watku |
| Baza danych | PostgreSQL 16 (kontener); SQLite jako tryb awaryjny do szybkiego uruchomienia bez Dockera |
| Technologia znana grupie | Python 3.12 + FastAPI + Jinja2 + SQLAlchemy |
| Cloud (GCP/AWS/**Azure**) | Azure + Azure DevOps - wybrane jako docelowe srodowisko (L3-L6) |

## 3. Stos technologiczny i uzasadnienie

| Warstwa | Technologia | Uzasadnienie |
| --- | --- | --- |
| Backend | Python 3.12, FastAPI | jezyk znany calej grupie, czytelny kod, wbudowana walidacja wejscia |
| Widoki | Jinja2 (SSR), czysty CSS | autoescaping domyslnie wlaczony (ochrona przed XSS), brak zaleznosci frontendowych do audytu |
| ORM / baza | SQLAlchemy 2.0, PostgreSQL 16 | zapytania parametryzowane (ochrona przed SQL injection), latwa migracja na Azure Database for PostgreSQL |
| Hasla | Argon2id (`argon2-cffi`) | rekomendacja OWASP Password Storage Cheat Sheet |
| Uruchomienie | Docker Compose: nginx + aplikacja + baza | odwzorowanie docelowej architektury chmurowej juz lokalnie |
| CI/CD | Azure DevOps Pipelines | wymagane srodowisko; szkielet pipeline'u w repozytorium |

## 4. Model danych

`users` (konta, rola, licznik nieudanych logowan, blokada czasowa) -
`user_sessions` (skrot tokenu sesji, IP, user agent, czas zycia, uniewaznienie) -
`threads` (watki) - `posts` (wpisy w watkach) - `audit_log` (zdarzenia bezpieczenstwa).

## 5. Elementy bezpieczenstwa wdrozone juz na L1

- Hasla skladowane jako hasz Argon2id, minimum 10 znakow, odrzucanie hasel popularnych.
- Sesje po stronie serwera: w ciasteczku tylko losowy token (256 bitow), w bazie jego SHA-256;
  limit bezczynnosci 30 min, bezwzgledny czas zycia 12 h, rotacja tokenu CSRF po zalogowaniu.
- Ochrona CSRF (double-submit cookie) na wszystkich formularzach zmieniajacych stan.
- Blokada konta po 5 nieudanych probach logowania + limit tempa `/login` na nginx (5 req/min/IP).
- Jednolity komunikat bledu logowania i stale opoznienie (weryfikacja haszu "na pusto") -
  brak enumeracji uzytkownikow.
- Naglowki: CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
  `Permissions-Policy`, HSTS (po wlaczeniu TLS).
- Log audytowy zdarzen (rejestracja, logowanie udane/nieudane, wylogowanie, uniewaznienie sesji)
  i log dostepowy z `X-Request-ID`.
- Kontener: uzytkownik nieuprzywilejowany (UID 10001), system plikow `read-only`,
  `cap_drop: ALL`, `no-new-privileges`, baza bez portu wystawionego na hosta.

## 6. Przygotowanie do kolejnych laboratoriow

Aplikacja jest bezstanowa (sesje w bazie), konfigurowana wylacznie zmiennymi
srodowiskowymi i wystawia probe'y `/healthz` oraz `/readyz`, dzieki czemu
przeniesienie na Azure (L4) sprowadza sie do zbudowania infrastruktury - bez zmian
w kodzie. Szczegoly: `docs/architektura.md`, `docs/roadmap.md`, `infra/azure/README.md`.

## 7. Uruchomienie srodowiska DEV

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec app python -m scripts.seed_demo_data   # dane do prezentacji
# aplikacja: http://localhost:43117
```
