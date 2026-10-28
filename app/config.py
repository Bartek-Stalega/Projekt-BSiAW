import os
from pathlib import Path

# Konfiguracja czytana ze zmiennych srodowiskowych - ten sam obraz kontenera
# dziala lokalnie i (pozniej) w chmurze, bez zmian w kodzie.

APP_NAME = "Folium"
TAGLINE = "Rząd nie chce żebyś o tym wiedział"
GROUP_LABEL = "BSiAW, grupa 1"
# Oficjalny sklad grupy (pokazywany w stopce).
AUTHORS = (
    "Bartosz Stalęga",
    "Julia Aranowska",
    "Dominik Baryła",
    "Julek Jarzembowski",
)
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
MAX_BODY_LENGTH = 8000

# Publiczny URL aplikacji (linki w mailach).
PUBLIC_BASE_URL = os.getenv("APP_PUBLIC_BASE_URL", "http://localhost:43117").rstrip("/")

# SMTP (w DEV: Mailhog).
SMTP_HOST = os.getenv("APP_SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("APP_SMTP_PORT", "1025"))
SMTP_FROM = os.getenv("APP_SMTP_FROM", "noreply@folium.local")

# Upload obrazkow.
UPLOAD_DIR = Path(os.getenv("APP_UPLOAD_DIR", "uploads"))
MAX_UPLOAD_BYTES = int(os.getenv("APP_MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

PASSWORD_RESET_TTL_SECONDS = int(os.getenv("APP_PASSWORD_RESET_TTL", str(60 * 60)))
