# Plan L1-L9

| Lab | Termin | Zakres | Stan |
| --- | --- | --- | --- |
| **L1** | 2026-10-22 | Wybor aplikacji i implementacja | **gotowe** - forum z logowaniem, PostgreSQL, Docker Compose, sprawozdanie |
| **L2** | 2026-10-29 | Funkcjonalnosc w srodowisku DEV | srodowisko DEV dziala; do zrobienia prezentacja i ewentualne drobne funkcje (paginacja, usuwanie wlasnego wpisu) |
| **L3** | 2026-11-05 | Projekt architektury cloud | szkic w `docs/architektura.md` i `infra/azure/README.md`; do zrobienia schematy, wybor SKU, domena i certyfikat |
| **L4** | 2026-11-14 | Implementacja architektury | do zrobienia: Container Apps, PostgreSQL Flexible Server, Application Gateway, DNS, migracje bazy |
| **L5** | 2026-11-18 | Proces CI/CD | szkielet `pipelines/azure-pipelines.yml` (lint, testy, build obrazu); do zrobienia publikacja do ACR i deploy |
| **L6** | 2026-11-26 | Bezpieczenstwo w CI/CD | do zrobienia: SAST (Bandit/Semgrep), skan obrazu (Trivy), skan zaleznosci, DAST (ZAP), sekrety w Key Vault |
| **L7** | 2026-12-03 | Bezpieczenstwo kodu i konfiguracji | do zrobienia: CSRF, naglowki (CSP, HSTS), limit prob logowania, monitoring sesji, WAF, CDN, anty-DDoS |
| **L8** | 2026-12-10 | Hardening infrastruktury | do zrobienia: CIS Benchmark dla Dockera i PostgreSQL, Azure Security Benchmark, hardening kontenerow |
| **L9** | 2026-12-17 | Testy rozwiazania | do zrobienia: nmap, sslscan, nikto, dirb, hydra, testy manualne wg OWASP Top 10 |
| **Zaliczenie** | 2027-01-14 | Prezentacja grupy 4 | dokumentacja w `docs/`, podzial czesci miedzy czlonkow grupy |

## Co swiadomie zostalo na pozniej

Na L1 aplikacja ma tylko to, co wynika wprost z wymagan: logowanie z sesja, forum
i baze. Zabezpieczenia aplikacyjne (CSRF, naglowki, limity logowania, monitoring)
to temat L7, bramki bezpieczenstwa w pipelinie - L6, a hardening srodowiska - L8.
Dzieki temu na prezentacjach widac roznice miedzy stanem "przed" i "po".

## Decyzje ulatwiajace przejscie do chmury

1. **Konfiguracja ze zmiennych srodowiskowych** - ten sam obraz dziala lokalnie
   i w Azure, bez przebudowy.
2. **Sesja w podpisanym ciasteczku** - aplikacja nie trzyma stanu w pamieci, wiec
   skalowanie do kilku instancji nie wymaga sticky sessions.
3. **Endpoint `/healthz`** - gotowy pod health probe load balancera.
4. **PostgreSQL od poczatku** - ta sama baza co docelowo w chmurze, bez niespodzianek
   przy migracji.

## Dlug techniczny

- Tabele tworzy `Base.metadata.create_all()` - przed L4 trzeba wprowadzic migracje
  (Alembic) uruchamiane z pipeline'u.
- Brak paginacji listy watkow - przy wiekszej liczbie wpisow do dolozenia na L2.
