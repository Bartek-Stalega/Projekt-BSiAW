from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app import __version__
from app.config import get_settings
from app.dependencies import DbDep

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/healthz", include_in_schema=False)
def liveness() -> dict:
    """Liveness probe - nie dotyka bazy, zeby LB nie ubijal instancji przy awarii DB."""
    return {"status": "ok", "version": __version__, "environment": settings.environment}


@router.get("/readyz", include_in_schema=False)
def readiness(db: DbDep, response: Response) -> dict:
    """Readiness probe dla load balancera (L3) - sprawdza polaczenie z baza."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - szczegoly trafiaja do logu, nie do klienta
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "degraded", "database": "unavailable"}
    return {"status": "ok", "database": "ok"}
