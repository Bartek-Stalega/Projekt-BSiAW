# Infrastruktura Azure (L3-L4)

Katalog na kod infrastruktury (Bicep lub Terraform). Na etapie L1 sa tu tylko
notatki - zasoby powstana na L3 (projekt) i L4 (implementacja).

## Mapowanie lokalnego srodowiska na Azure

| Lokalnie (`docker-compose.yml`) | Azure |
| --- | --- |
| kontener `app` | Azure Container Apps (obraz z Azure Container Registry) |
| kontener `db` | Azure Database for PostgreSQL Flexible Server |
| port 43117 na hoscie | Application Gateway + Azure DNS (domena, certyfikat TLS) |
| zmienne z `.env` | App Settings, sekrety w Key Vault |
| logi na stdout | Log Analytics / Application Insights |

## Co w aplikacji jest juz przygotowane

- konfiguracja wylacznie ze zmiennych srodowiskowych (`APP_SECRET_KEY`, `APP_DATABASE_URL`,
  `APP_COOKIE_SECURE`) - bez zmian w kodzie przy przenoszeniu,
- sesja w podpisanym ciasteczku zamiast w pamieci procesu - mozna uruchomic wiele
  instancji za load balancerem,
- endpoint `/healthz` pod health probe,
- `APP_COOKIE_SECURE=true` wlacza flage `Secure` na ciasteczku po wpieciu TLS.

## Planowane pliki

```
infra/azure/
├── main.bicep          # grupa zasobow i powiazania
└── modules/
    ├── database.bicep      # PostgreSQL Flexible Server
    ├── container-app.bicep  # Container Apps
    └── gateway.bicep        # Application Gateway + certyfikat
```
