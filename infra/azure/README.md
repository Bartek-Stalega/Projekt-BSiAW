# Infrastruktura Azure (L3-L4)

Katalog zarezerwowany na kod infrastruktury (Bicep / Terraform). Na etapie **L1**
jest tu wylacznie projekt docelowy - zasoby powstana na laboratorium L3 (projekt)
i L4 (implementacja). Aplikacja jest juz przygotowana tak, aby przeniesienie
nie wymagalo zmian w kodzie.

## Mapowanie: lokalny Docker -> Azure

| Element lokalny (`docker-compose.yml`) | Odpowiednik w Azure | Uwagi |
| --- | --- | --- |
| `proxy` (nginx, port 43117) | Application Gateway v2 + WAF | terminacja TLS, reguly OWASP CRS (L7) |
| `app` (uvicorn, 1-N kontenerow) | Azure Container Apps | skalowanie HTTP, probe `/healthz` i `/readyz` |
| `db` (postgres:16-alpine) | Azure Database for PostgreSQL Flexible Server | Private Endpoint, backupy, replika do odczytu |
| zmienne w `.env` | App Settings + Key Vault | sekrety przez referencje do Key Vault |
| obraz budowany lokalnie | Azure Container Registry | tag = `Build.BuildId` z pipeline'u |
| logi na stdout | Log Analytics / Application Insights | korelacja po naglowku `X-Request-ID` |
| brak | Azure DNS + managed certificate | domena `bsiaw-gr4.<domena>.pl`, cert poza serwerem aplikacyjnym |

## Co w aplikacji jest juz "cloud ready"

- **Brak stanu w procesie aplikacji** - sesje leza w bazie (tabela `user_sessions`),
  wiec load balancer nie potrzebuje sticky sessions, a skalowanie do N instancji
  nie wylogowuje uzytkownikow.
- **Konfiguracja wylacznie ze zmiennych srodowiskowych** (prefiks `APP_`) -
  ten sam obraz dziala lokalnie i w chmurze, bez przebudowy.
- **Dedykowane probe'y** `/healthz` (liveness, nie dotyka bazy) i `/readyz`
  (readiness, sprawdza polaczenie z baza).
- **Obsluga naglowkow proxy** (`X-Forwarded-For`, `X-Forwarded-Proto`) - realne IP
  klienta trafia do logow audytowych takze zza Application Gateway.
- **`APP_COOKIE_SECURE=true`** wlacza `Secure` na ciasteczkach i naglowek HSTS -
  jedyna zmiana potrzebna po wpieciu TLS na warstwie brzegowej.

## Planowane pliki

```
infra/azure/
├── main.bicep              # grupa zasobow, sieci, zaleznosci (L4)
├── modules/
│   ├── network.bicep       # VNet, subnety, NSG, Private Endpoint
│   ├── database.bicep      # PostgreSQL Flexible Server
│   ├── container-app.bicep # Container Apps Environment + aplikacja
│   └── gateway.bicep       # Application Gateway + WAF + certyfikat
└── parameters/
    ├── dev.bicepparam
    └── prod.bicepparam
```
