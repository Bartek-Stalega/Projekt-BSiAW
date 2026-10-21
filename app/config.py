from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Konfiguracja aplikacji w stylu 12-factor.

    Wszystkie wartosci pochodza ze zmiennych srodowiskowych z prefiksem ``APP_``,
    dzieki czemu ten sam obraz kontenera dziala lokalnie (docker compose),
    jak i w chmurze (App Settings / Key Vault w Azure).
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SecForum"
    environment: Literal["local", "dev", "test", "prod"] = "local"
    debug: bool = False

    # Klucz uzywany do podpisywania tokenow pomocniczych. W chmurze pobierany
    # z Azure Key Vault, nigdy z repozytorium.
    secret_key: str = "local-dev-secret-change-me"  # noqa: S105

    # SQLite pozwala uruchomic projekt bez Dockera, docker compose i Azure
    # podstawiaja tu PostgreSQL przez zmienna srodowiskowa.
    database_url: str = "sqlite:///./data/secforum.db"

    session_cookie_name: str = "secforum_session"
    csrf_cookie_name: str = "secforum_csrf"
    session_absolute_ttl_minutes: int = 12 * 60
    session_idle_timeout_minutes: int = 30
    # Za reverse proxy / Application Gateway z TLS ustawiamy APP_COOKIE_SECURE=true.
    cookie_secure: bool = False

    login_max_attempts: int = 5
    login_lockout_minutes: int = 10

    max_thread_title_length: int = 120
    max_post_body_length: int = 2000
    page_size: int = 20

    log_level: str = "INFO"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
