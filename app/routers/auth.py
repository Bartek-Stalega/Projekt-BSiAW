from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select

from app.config import get_settings
from app.dependencies import (
    CsrfDep,
    CurrentUserDep,
    DbDep,
    OptionalUserDep,
    SessionDep,
    client_ip,
)
from app.models import User, UserSession, utcnow
from app.security import (
    generate_token,
    hash_password,
    needs_rehash,
    validate_registration,
    verify_password,
)
from app.services import audit
from app.services import sessions as session_service
from app.web import render

router = APIRouter(tags=["auth"])
settings = get_settings()

GENERIC_LOGIN_ERROR = "Nieprawidlowa nazwa uzytkownika lub haslo."

# Hasz "na pusto": weryfikujemy go, gdy konto nie istnieje, zeby czas odpowiedzi
# nie zdradzal, czy dana nazwa uzytkownika jest zarejestrowana.
_DUMMY_PASSWORD_HASH = hash_password(generate_token(16))


def _set_session_cookie(response: RedirectResponse, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_absolute_ttl_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


@router.get("/register")
def register_form(request: Request, user: OptionalUserDep):
    if user:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return render(request, "register.html")


@router.post("/register")
def register(
    request: Request,
    db: DbDep,
    _csrf: CsrfDep,
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    password_confirm: Annotated[str, Form()],
):
    username = username.strip()
    email = email.strip().lower()

    error = validate_registration(username, email, password, password_confirm)
    if error is None:
        taken = db.scalar(
            select(func.count(User.id)).where(
                (func.lower(User.username) == username.lower()) | (User.email == email)
            )
        )
        if taken:
            error = "Taka nazwa uzytkownika lub e-mail jest juz zajety."

    if error:
        return render(
            request,
            "register.html",
            {"error": error, "form": {"username": username, "email": email}},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = User(username=username, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    audit.record(db, "user_registered", username=username, ip_address=client_ip(request))
    return RedirectResponse("/login?msg=registered", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_form(request: Request, user: OptionalUserDep):
    if user:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return render(request, "login.html")


@router.post("/login")
def login(
    request: Request,
    db: DbDep,
    _csrf: CsrfDep,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    username = username.strip()
    ip = client_ip(request)
    user = db.scalar(select(User).where(func.lower(User.username) == username.lower()))

    def failure(message: str, event: str, detail: str | None = None):
        audit.record(db, event, username=username, ip_address=ip, detail=detail)
        return render(
            request,
            "login.html",
            {"error": message, "form": {"username": username}},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if user is None:
        verify_password(_DUMMY_PASSWORD_HASH, password)
        return failure(GENERIC_LOGIN_ERROR, "login_failed", detail="unknown_user")

    if user.locked_until and user.locked_until > utcnow():
        return failure(
            "Konto jest tymczasowo zablokowane po nieudanych probach logowania.",
            "login_blocked",
            detail="account_locked",
        )

    if not user.is_active:
        return failure(GENERIC_LOGIN_ERROR, "login_failed", detail="inactive_account")

    if not verify_password(user.password_hash, password):
        user.failed_logins += 1
        if user.failed_logins >= settings.login_max_attempts:
            user.locked_until = utcnow() + timedelta(minutes=settings.login_lockout_minutes)
            user.failed_logins = 0
        db.commit()
        return failure(GENERIC_LOGIN_ERROR, "login_failed", detail="bad_password")

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    user.failed_logins = 0
    user.locked_until = None
    db.commit()

    _, token = session_service.create_session(
        db, user, ip_address=ip, user_agent=request.headers.get("user-agent")
    )
    audit.record(db, "login_success", username=user.username, ip_address=ip)

    response = RedirectResponse("/?msg=logged_in", status_code=status.HTTP_303_SEE_OTHER)
    _set_session_cookie(response, token)
    # Rotacja tokenu CSRF przy zmianie poziomu uprawnien.
    response.set_cookie(
        settings.csrf_cookie_name,
        generate_token(16),
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return response


@router.post("/logout")
def logout(request: Request, db: DbDep, _csrf: CsrfDep, session: SessionDep):
    if session is not None:
        session_service.revoke_session(db, session)
        audit.record(db, "logout", username=session.user.username, ip_address=client_ip(request))
    response = RedirectResponse("/?msg=logged_out", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(settings.session_cookie_name, path="/")
    return response


@router.get("/account/sessions")
def account_sessions(request: Request, db: DbDep, user: CurrentUserDep, session: SessionDep):
    records = session_service.list_sessions(db, user.id)
    return render(
        request,
        "sessions.html",
        {
            "sessions": records,
            "current_session_id": session.id if session else None,
            "idle_timeout": settings.session_idle_timeout_minutes,
            "absolute_ttl": settings.session_absolute_ttl_minutes,
        },
    )


@router.post("/account/sessions/revoke-others")
def revoke_other_sessions(
    request: Request, db: DbDep, _csrf: CsrfDep, user: CurrentUserDep, session: SessionDep
):
    if session is not None:
        count = session_service.revoke_other_sessions(db, user.id, session.id)
        audit.record(
            db,
            "sessions_revoked",
            username=user.username,
            ip_address=client_ip(request),
            detail=f"count={count}",
        )
    return RedirectResponse(
        "/account/sessions?msg=sessions_revoked", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/account/sessions/{session_id}/revoke")
def revoke_single_session(
    request: Request,
    db: DbDep,
    _csrf: CsrfDep,
    user: CurrentUserDep,
    session: SessionDep,
    session_id: int,
):
    record = db.get(UserSession, session_id)
    if record is None or record.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono sesji")

    session_service.revoke_session(db, record)
    audit.record(
        db,
        "session_revoked",
        username=user.username,
        ip_address=client_ip(request),
        detail=f"session_id={session_id}",
    )

    if session is not None and record.id == session.id:
        response = RedirectResponse("/login?msg=logged_out", status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(settings.session_cookie_name, path="/")
        return response
    return RedirectResponse(
        "/account/sessions?msg=session_revoked", status_code=status.HTTP_303_SEE_OTHER
    )
