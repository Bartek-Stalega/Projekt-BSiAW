from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


def _engine_kwargs() -> dict:
    if settings.is_sqlite:
        db_path = settings.database_url.removeprefix("sqlite:///")
        if db_path not in {":memory:", ""}:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return {"connect_args": {"check_same_thread": False}}
    # pool_pre_ping chroni przed zerwanymi polaczeniami, gdy baza stoi
    # za load balancerem / jest zarzadzana (Azure Database for PostgreSQL).
    return {"pool_pre_ping": True, "pool_size": 5, "max_overflow": 10}


engine = create_engine(settings.database_url, echo=False, **_engine_kwargs())
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Tworzy schemat bazy.

    Na etapie L1/L2 wystarczy ``create_all``. Przed wdrozeniem w chmurze
    (L4) zastapimy to migracjami Alembic uruchamianymi z pipeline'u.
    """
    from app import models  # noqa: F401  (rejestracja modeli w metadata)

    Base.metadata.create_all(bind=engine)
