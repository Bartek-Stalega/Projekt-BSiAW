import os

# Konfiguracja czytana ze zmiennych srodowiskowych - ten sam obraz kontenera
# dziala lokalnie i (pozniej) w chmurze, bez zmian w kodzie.

APP_NAME = "SecForum"
ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "local")

# Klucz podpisujacy ciasteczko sesji. W chmurze bedzie pochodzil z Key Vault.
SECRET_KEY = os.getenv("APP_SECRET_KEY", "local-dev-secret-change-me")

# Lokalnie bez Dockera dziala SQLite, docker compose podstawia PostgreSQL.
DATABASE_URL = os.getenv("APP_DATABASE_URL", "sqlite:///./data/secforum.db")

SESSION_COOKIE = "secforum_session"
SESSION_MAX_AGE_SECONDS = int(os.getenv("APP_SESSION_MAX_AGE", str(8 * 60 * 60)))
# true dopiero, gdy ruch idzie po HTTPS.
COOKIE_SECURE = os.getenv("APP_COOKIE_SECURE", "false").lower() == "true"

MIN_PASSWORD_LENGTH = 8
MAX_TITLE_LENGTH = 120
MAX_BODY_LENGTH = 2000
