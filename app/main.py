import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import get_settings
from app.database import SessionLocal, init_db
from app.middleware import CsrfCookieMiddleware, RequestLogMiddleware, SecurityHeadersMiddleware
from app.routers import auth, forum, health
from app.services import sessions as session_service
from app.web import BASE_DIR, render

settings = get_settings()
logger = logging.getLogger("secforum")


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()
    with SessionLocal() as db:
        purged = session_service.purge_expired(db)
    logger.info(
        "start app=%s version=%s env=%s purged_sessions=%s",
        settings.app_name,
        __version__,
        settings.environment,
        purged,
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
        # Dokumentacja API wylaczona poza srodowiskiem lokalnym - mniejsza
        # powierzchnia ataku i mniej informacji dla rekonesansu.
        docs_url="/docs" if settings.environment in {"local", "dev"} else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.environment in {"local", "dev"} else None,
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CsrfCookieMiddleware)
    app.add_middleware(RequestLogMiddleware)

    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(forum.router)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        location = (exc.headers or {}).get("Location")
        if location:
            return RedirectResponse(location, status_code=exc.status_code)
        if "text/html" in request.headers.get("accept", ""):
            return render(
                request,
                "error.html",
                {"status_code": exc.status_code, "message": exc.detail},
                status_code=exc.status_code,
            )
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Szczegoly walidacji zostaja w logach - uzytkownik dostaje ogolny komunikat.
        logger.warning("validation_error path=%s errors=%s", request.url.path, exc.errors())
        if "text/html" in request.headers.get("accept", ""):
            return render(
                request,
                "error.html",
                {"status_code": 400, "message": "Nieprawidlowe dane formularza."},
                status_code=400,
            )
        return JSONResponse({"detail": "Nieprawidlowe dane wejsciowe"}, status_code=400)

    return app


app = create_app()
