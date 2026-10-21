from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import (
    APP_NAME,
    COOKIE_SECURE,
    ENVIRONMENT,
    SECRET_KEY,
    SESSION_COOKIE,
    SESSION_MAX_AGE_SECONDS,
)
from app.db import init_db
from app.routers import auth, forum
from app.templating import BASE_DIR, render


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)

# Sesja uzytkownika: podpisane ciasteczko (HttpOnly). Aplikacja nie trzyma stanu
# w pamieci procesu, wiec mozna uruchomic wiele instancji za load balancerem.
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie=SESSION_COOKIE,
    max_age=SESSION_MAX_AGE_SECONDS,
    https_only=COOKIE_SECURE,
    same_site="lax",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(auth.router)
app.include_router(forum.router)


@app.get("/healthz", include_in_schema=False)
def healthz() -> dict:
    """Prosty endpoint dla Dockera i (pozniej) load balancera w chmurze."""
    return {"status": "ok", "environment": ENVIRONMENT}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    location = (exc.headers or {}).get("Location")
    if location:
        return RedirectResponse(location, status_code=exc.status_code)
    if "text/html" in request.headers.get("accept", ""):
        return render(
            request,
            "error.html",
            status_code=exc.status_code,
            code=exc.status_code,
            message=exc.detail,
        )
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
