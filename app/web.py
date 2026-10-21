from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app import __version__
from app.config import get_settings

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

settings = get_settings()


def _format_datetime(value) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


templates.env.filters["dt"] = _format_datetime

# Komunikaty sa wybierane po kluczu z whitelisty - do szablonu nigdy nie trafia
# tekst podany przez uzytkownika w query stringu.
FLASH_MESSAGES: dict[str, tuple[str, str]] = {
    "registered": ("success", "Konto zalozone. Mozesz sie zalogowac."),
    "logged_in": ("success", "Zalogowano pomyslnie."),
    "logged_out": ("info", "Wylogowano. Sesja zostala uniewazniona."),
    "login_required": ("info", "Zaloguj sie, aby kontynuowac."),
    "session_expired": ("info", "Sesja wygasla. Zaloguj sie ponownie."),
    "thread_created": ("success", "Watek zostal utworzony."),
    "post_created": ("success", "Odpowiedz zostala dodana."),
    "sessions_revoked": ("success", "Pozostale sesje zostaly uniewaznione."),
    "session_revoked": ("success", "Sesja zostala uniewazniona."),
}


def flash_from_query(request: Request) -> tuple[str, str] | None:
    key = request.query_params.get("msg")
    if key is None:
        return None
    return FLASH_MESSAGES.get(key)


def render(request: Request, template: str, context: dict | None = None, status_code: int = 200):
    payload = {
        "request": request,
        "app_name": settings.app_name,
        "app_version": __version__,
        "environment": settings.environment,
        "current_user": getattr(request.state, "user", None),
        "csrf_token": getattr(request.state, "csrf_token", ""),
        "flash": flash_from_query(request),
    }
    payload.update(context or {})
    return templates.TemplateResponse(request, template, payload, status_code=status_code)
