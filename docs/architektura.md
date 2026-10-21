# Architektura SecForum

## 1. Srodowisko lokalne (L1-L2, Docker Compose)

```
                    host: http://localhost:43117
                               |
                   +-----------v-----------+      siec "edge"
                   |   nginx (proxy)       |
                   |  - limit req /login   |
                   |  - naglowki proxy     |
                   |  - miejsce na TLS/WAF |
                   +-----------+-----------+
                               | http://app:8000
                   +-----------v-----------+      siec "edge" + "backend"
                   |   app (uvicorn)       |      read-only, cap_drop ALL,
                   |   FastAPI + Jinja2    |      UID 10001, N instancji
                   |  /healthz  /readyz    |
                   +-----------+-----------+
                               | postgresql+psycopg
                   +-----------v-----------+      siec "backend" (internal)
                   |   db (PostgreSQL 16)  |      brak portu na hoscie
                   |   wolumen db-data     |
                   +-----------------------+
```

Siec `backend` jest oznaczona jako `internal` - kontener bazy nie ma trasy do
internetu ani portu opublikowanego na hoscie. Jedynym wejsciem do systemu jest
port reverse proxy.

## 2. Srodowisko docelowe (L3-L4, Azure)

```
   Internet
      |
   Azure DNS  (bsiaw-gr4.<domena>.pl)
      |
   Application Gateway v2 + WAF  <-- certyfikat TLS (poza serwerem aplikacyjnym)
      |  reguly OWASP CRS, anty-DDoS
      |
   Azure Container Apps  (autoskalowanie HTTP, N replik, probe /healthz, /readyz)
      |  tozsamosc zarzadzana (Managed Identity)
      |
   +--+-----------------------------+
   |                                |
   Key Vault                 Azure Database for PostgreSQL
   (sekrety, connection      Flexible Server (Private Endpoint,
    string, klucze)           backupy, replika do odczytu)

   Obserwowalnosc: Log Analytics + Application Insights (korelacja po X-Request-ID)
   Rejestr obrazow: Azure Container Registry (obraz z pipeline'u Azure DevOps)
```

## 3. Przeplyw uwierzytelnienia i sesji

1. `POST /login` - weryfikacja haszu Argon2id; przy bledzie jednolity komunikat
   i inkrementacja licznika nieudanych prob (blokada po 5 probach na 10 minut).
2. Sukces: generowany jest token sesji (`secrets.token_urlsafe(32)`). Do bazy trafia
   **wylacznie SHA-256 tokenu**, do przegladarki ciasteczko `HttpOnly`, `SameSite=Lax`
   (oraz `Secure` przy `APP_COOKIE_SECURE=true`). Token CSRF jest rotowany.
3. Kazde zadanie: token z ciasteczka -> skrot -> wyszukanie sesji -> kontrola
   `revoked_at`, `expires_at` (12 h) i bezczynnosci (30 min) -> odswiezenie `last_seen_at`.
4. `POST /logout` oraz `/account/sessions/*` ustawiaja `revoked_at` - uniewaznienie
   dziala natychmiast na wszystkich instancjach aplikacji, bo stan jest w bazie.

Konsekwencja dla skalowania: aplikacja jest bezstanowa, wiec load balancer nie
potrzebuje sticky sessions, a dodanie repliki nie wylogowuje uzytkownikow.

## 4. Model danych

```
users 1---* threads 1---* posts
  |              \________*  (autor wpisu)
  *
user_sessions          audit_log (bez FK - log zdarzen, takze dla nieznanych kont)
```

| Tabela | Kluczowe kolumny | Rola |
| --- | --- | --- |
| `users` | `username`, `email`, `password_hash`, `role`, `failed_logins`, `locked_until` | konta i stan blokady |
| `user_sessions` | `token_hash`, `user_id`, `created_at`, `last_seen_at`, `expires_at`, `revoked_at`, `ip_address`, `user_agent` | sesje serwerowe i ich monitoring |
| `threads` | `title`, `author_id`, `created_at` | watki forum |
| `posts` | `thread_id`, `author_id`, `body`, `created_at` | wpisy w watkach |
| `audit_log` | `event`, `username`, `ip_address`, `detail`, `created_at` | zdarzenia bezpieczenstwa |

## 5. Mapa endpointow

| Metoda | Sciezka | Dostep | Opis |
| --- | --- | --- | --- |
| GET | `/` | publiczny | lista watkow |
| GET | `/threads/{id}` | publiczny | watek z wpisami |
| GET/POST | `/register` | publiczny | rejestracja konta |
| GET/POST | `/login` | publiczny | logowanie (limit tempa na nginx) |
| POST | `/logout` | zalogowany | uniewaznienie biezacej sesji |
| GET/POST | `/threads/new` | zalogowany | zalozenie watku |
| POST | `/threads/{id}/posts` | zalogowany | odpowiedz w watku |
| GET | `/account/sessions` | zalogowany | podglad aktywnych sesji |
| POST | `/account/sessions/revoke-others` | zalogowany | wylogowanie pozostalych urzadzen |
| POST | `/account/sessions/{id}/revoke` | zalogowany (wlasciciel) | uniewaznienie wskazanej sesji |
| GET | `/healthz`, `/readyz` | infrastruktura | probe'y dla LB |

## 6. Struktura repozytorium

```
app/            kod aplikacji (routery, modele, warstwa bezpieczenstwa, szablony)
infra/nginx/    konfiguracja reverse proxy (lokalny odpowiednik App Gateway)
infra/azure/    projekt infrastruktury chmurowej (L3-L4)
pipelines/      szkielet pipeline'u Azure DevOps (L5-L6)
scripts/        skrypty pomocnicze (dane demo)
tests/          testy funkcjonalne i bezpieczenstwa
docs/           sprawozdania i dokumentacja projektowa
```
