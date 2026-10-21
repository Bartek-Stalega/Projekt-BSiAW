# Architektura SecForum

## 1. Srodowisko lokalne (L1-L2)

```
   przegladarka
        |  http://localhost:43117
   +----v------------------+
   |  app (kontener)       |   FastAPI + Jinja2, uvicorn na porcie 8000
   |  /healthz             |   uzytkownik nieuprzywilejowany
   +----+------------------+
        |  postgresql+psycopg
   +----v------------------+
   |  db (kontener)        |   PostgreSQL 16, wolumen db-data
   |                       |   bez portu opublikowanego na hoscie
   +-----------------------+
```

Cale srodowisko stawia `docker compose up --build -d`. Konfiguracja idzie przez
zmienne srodowiskowe (`APP_SECRET_KEY`, `APP_DATABASE_URL`), wiec ten sam obraz
zadziala pozniej w chmurze bez zmian w kodzie.

## 2. Docelowe srodowisko w Azure (projekt na L3, wdrozenie na L4)

```
   Internet -> Azure DNS -> Application Gateway (TLS, pozniej WAF)
                                   |
                           Azure Container Apps  (obraz z Azure Container Registry)
                                   |
                        Azure Database for PostgreSQL
```

Mapowanie uslug: kontener `app` -> Container Apps, kontener `db` -> PostgreSQL
Flexible Server, zmienne srodowiskowe -> App Settings / Key Vault, certyfikat TLS ->
Application Gateway (czyli poza serwerem aplikacyjnym, zgodnie z wymaganiem L3).

Szczegoly i planowane pliki IaC: [`infra/azure/README.md`](../infra/azure/README.md).

## 3. Sesja uzytkownika

Po poprawnym logowaniu do ciasteczka trafia podpisane `user_id` (Starlette
`SessionMiddleware`, podpis kluczem `APP_SECRET_KEY`). Aplikacja nie trzyma nic
w pamieci procesu, wiec mozna uruchomic kilka instancji za load balancerem i nie
trzeba wlaczac sticky sessions. Ciasteczko jest `HttpOnly` i wygasa po 8 godzinach;
flaga `Secure` wlacza sie przez `APP_COOKIE_SECURE=true`, gdy ruch pojdzie po HTTPS.

## 4. Model danych

```
users 1---* threads 1---* posts
  \______________________*   (autor wpisu)
```

| Tabela | Kolumny |
| --- | --- |
| `users` | `id`, `username`, `password_hash`, `created_at` |
| `threads` | `id`, `title`, `author_id`, `created_at` |
| `posts` | `id`, `thread_id`, `author_id`, `body`, `created_at` |

## 5. Struktura kodu

```
app/
  config.py        ustawienia ze zmiennych srodowiskowych
  db.py            silnik SQLAlchemy, sesja bazy, tworzenie tabel
  models.py        User, Thread, Post
  deps.py          zaleznosci FastAPI: baza, zalogowany uzytkownik
  templating.py    Jinja2 + wspolny kontekst szablonow
  routers/auth.py  rejestracja, logowanie, wylogowanie
  routers/forum.py lista watkow, nowy watek, odpowiedzi
  templates/       szablony HTML
  static/          styl i favicon
```
