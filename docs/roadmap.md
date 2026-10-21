# Plan prac L1-L9 i stan przygotowania repozytorium

Terminy wg harmonogramu prowadzacego. Kolumna "Co juz jest" pokazuje, co z danego
laboratorium zostalo przygotowane z wyprzedzeniem na etapie L1.

| Lab | Termin | Zakres | Co juz jest w repozytorium | Co trzeba dorobic |
| --- | --- | --- | --- | --- |
| **L1** | 2026-10-22 | Wybor aplikacji i implementacja | **Gotowe:** forum z logowaniem i sesjami, PostgreSQL, Docker Compose, sprawozdanie | - |
| **L2** | 2026-10-29 | Funkcjonalnosc w srodowisku DEV | pelne srodowisko DEV w Dockerze, dane demo, testy | prezentacja dzialania, ewentualne drobne funkcje (edycja/usuwanie wpisu, paginacja) |
| **L3** | 2026-11-05 | Projekt architektury cloud | `docs/architektura.md` (sekcja Azure), `infra/azure/README.md` | schematy do dokumentacji, wybor SKU, projekt sieci i domeny |
| **L4** | 2026-11-14 | Implementacja architektury | aplikacja bezstanowa, probe'y, konfiguracja z env | Bicep: VNet, PostgreSQL Flexible Server, Container Apps, App Gateway + TLS, DNS |
| **L5** | 2026-11-18 | Proces CI/CD | `pipelines/azure-pipelines.yml` (stage Quality + Build) | stage Deploy, ACR, srodowiska dev/prod, approvals |
| **L6** | 2026-11-26 | Bezpieczenstwo w CI/CD | kroki Bandit i pip-audit, miejsce na Trivy | Semgrep/Checkov, Trivy (blokujacy), OWASP ZAP (DAST), sekrety z Key Vault, podpisywanie obrazow |
| **L7** | 2026-12-03 | Bezpieczenstwo kodu i konfiguracji | CSP i pozostale naglowki, CSRF, Argon2id, blokada konta, monitoring sesji, log audytowy | WAF (OWASP CRS), CDN/Front Door, anty-DDoS, alerty w Azure Monitor, rate limiting na brzegu |
| **L8** | 2026-12-10 | Hardening infrastruktury | kontener non-root, read-only FS, `cap_drop: ALL`, siec `internal`, nginx bez `server_tokens` | CIS Benchmark dla Dockera i PostgreSQL, Azure Security Benchmark, raport z `docker-bench-security` |
| **L9** | 2026-12-17 | Testy rozwiazania | testy funkcjonalne i negatywne (CSRF, XSS, blokada konta, dostep anonimowy) | nmap, sslscan, nikto, dirb, hydra, ZAP, testy manualne wg OWASP Top 10 |
| **Zaliczenie** | 2027-01-14 | Prezentacja grupy 4 | dokumentacja w `docs/`, skrypty wdrozeniowe w repozytorium | prezentacja (20-30 min), podzial czesci miedzy czlonkow grupy |

## Decyzje projektowe podjete pod katem pozniejszych etapow

1. **Sesje w bazie, nie w pamieci procesu** - warunek skalowania za load balancerem (L3/L4)
   i monitoringu sesji (L7).
2. **Konfiguracja wylacznie przez zmienne `APP_*`** - ten sam obraz w kazdym srodowisku;
   w Azure wartosci pochodza z App Settings i Key Vault (L6).
3. **Reverse proxy juz lokalnie** - sciezka zadania jest taka sama jak w chmurze,
   wiec naglowki, limity i TLS testujemy bez niespodzianek po migracji (L4/L7).
4. **Osobne `/healthz` i `/readyz`** - liveness nie zalezy od bazy, zeby awaria bazy
   nie powodowala restartow instancji (L4).
5. **Obraz non-root, read-only, bez zbednych pakietow** - punkt wyjscia do CIS Docker
   Benchmark (L8).
6. **Log audytowy od poczatku** - zdarzenia bezpieczenstwa beda zrodlem alertow (L7)
   i dowodem w testach (L9).

## Dlug techniczny do splacenia przed chmura

- `Base.metadata.create_all()` zamiast migracji - przed L4 wprowadzic Alembic
  i uruchamiac migracje jako osobny krok pipeline'u.
- Limit tempa logowania dziala per instancja nginx; na brzegu w Azure trzeba go
  ustawic na Application Gateway / Front Door.
- Brak rol administracyjnych (kolumna `role` istnieje, ale nie jest wykorzystywana) -
  do rozwazenia przy moderacji tresci (L2/L7).
