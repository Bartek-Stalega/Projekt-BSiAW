from typing import Annotated

from fastapi import Depends, Form, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.database import get_db
from app.models import User, UserSession
from app.security import tokens_match
from app.services import sessions as session_service

settings = get_settings()

DbDep = Annotated[DbSession, Depends(get_db)]


def client_ip(request: Request) -> str | None:
    """Adres klienta.

    Lokalnie nginx, a w chmurze Application Gateway przekazuja oryginalne IP
    w ``X-Forwarded-For``. Ufamy wylacznie pierwszemu wpisowi i tylko dlatego,
    ze aplikacja nie jest wystawiona bezposrednio do internetu.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    return request.client.host if request.client else None


def get_current_session(request: Request, db: DbDep) -> UserSession | None:
    token = request.cookies.get(settings.session_cookie_name)
    record = session_service.get_valid_session(db, token)
    request.state.session = record
    return record


SessionDep = Annotated[UserSession | None, Depends(get_current_session)]


def get_current_user(request: Request, session: SessionDep) -> User | None:
    user = session.user if session and session.user.is_active else None
    request.state.user = user
    return user


OptionalUserDep = Annotated[User | None, Depends(get_current_user)]


def require_user(user: OptionalUserDep) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login?msg=login_required"},
        )
    return user


CurrentUserDep = Annotated[User, Depends(require_user)]


def verify_csrf(request: Request, csrf_token: Annotated[str, Form()] = "") -> None:  # nosec B107
    """Double-submit cookie: wartosc z formularza musi zgadzac sie z ciasteczkiem.

    Pusty domyslny parametr to brak tokenu w formularzu - taki request zostanie
    odrzucony, a nie przepuszczony (Bandit raportuje go jako B107 bledem).
    """
    cookie_token = request.cookies.get(settings.csrf_cookie_name)
    if not tokens_match(cookie_token, csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Nieprawidlowy token CSRF"
        )


CsrfDep = Annotated[None, Depends(verify_csrf)]
