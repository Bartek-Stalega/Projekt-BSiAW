import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.config import MIN_PASSWORD_LENGTH, PASSWORD_RESET_TTL_SECONDS
from app.deps import DbDep, UserDep
from app.mail import send_password_reset
from app.models import PasswordResetToken, User, utcnow
from app.templating import render

router = APIRouter(tags=["auth"])
hasher = PasswordHasher()


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@router.get("/register")
def register_form(request: Request, user: UserDep):
    if user:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return render(request, "register.html")


@router.post("/register")
def register(
    request: Request,
    db: DbDep,
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    username = username.strip()
    email = email.strip().lower()

    error = None
    if not 3 <= len(username) <= 32:
        error = "Nazwa uzytkownika musi miec od 3 do 32 znakow."
    elif "@" not in email or len(email) > 255:
        error = "Podaj poprawny adres e-mail."
    elif len(password) < MIN_PASSWORD_LENGTH:
        error = f"Haslo musi miec co najmniej {MIN_PASSWORD_LENGTH} znakow."
    elif db.scalar(select(User).where(User.username == username)):
        error = "Taka nazwa uzytkownika jest juz zajeta."
    elif db.scalar(select(User).where(User.email == email)):
        error = "Ten adres e-mail jest juz zajety."

    if error:
        return render(
            request,
            "register.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=error,
            username=username,
            email=email,
        )

    db.add(
        User(
            username=username,
            email=email,
            password_hash=hasher.hash(password),
        )
    )
    db.commit()
    request.session["flash"] = "Konto zalozone. Mozesz sie zalogowac."
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login")
def login_form(request: Request, user: UserDep):
    if user:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return render(request, "login.html")


@router.post("/login")
def login(
    request: Request,
    db: DbDep,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    username = username.strip()
    user = db.scalar(select(User).where(User.username == username))

    try:
        if user is None or not user.is_active:
            raise VerificationError
        hasher.verify(user.password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return render(
            request,
            "login.html",
            status_code=status.HTTP_401_UNAUTHORIZED,
            error="Nieprawidlowa nazwa uzytkownika lub haslo.",
            username=username,
        )

    request.session["user_id"] = user.id
    request.session["flash"] = f"Zalogowano jako {user.username}."
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    request.session["flash"] = "Wylogowano."
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/forgot-password")
def forgot_password_form(request: Request, user: UserDep):
    if user:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return render(request, "forgot_password.html")


@router.post("/forgot-password")
def forgot_password(request: Request, db: DbDep, email: Annotated[str, Form()]):
    email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))

    # Zawsze ten sam komunikat - nie zdradzamy czy email istnieje.
    flash = "Jesli konto istnieje, wyslalismy link do resetu hasla."

    if user and user.is_active:
        raw = secrets.token_urlsafe(32)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=_hash_token(raw),
                expires_at=utcnow() + timedelta(seconds=PASSWORD_RESET_TTL_SECONDS),
            )
        )
        db.commit()
        try:
            send_password_reset(user.email, raw)
        except OSError:
            request.session["flash"] = "Nie udalo sie wyslac maila. Sprobuj pozniej."
            return RedirectResponse("/forgot-password", status_code=status.HTTP_303_SEE_OTHER)

    request.session["flash"] = flash
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/reset-password")
def reset_password_form(request: Request, db: DbDep, token: str = ""):
    if not token or _find_valid_token(db, token) is None:
        return render(
            request,
            "reset_password.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            error="Link jest nieprawidlowy lub wygasl.",
            token="",
        )
    return render(request, "reset_password.html", token=token)


@router.post("/reset-password")
def reset_password(
    request: Request,
    db: DbDep,
    token: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    row = _find_valid_token(db, token)
    if row is None:
        return render(
            request,
            "reset_password.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            error="Link jest nieprawidlowy lub wygasl.",
            token="",
        )

    if len(password) < MIN_PASSWORD_LENGTH:
        return render(
            request,
            "reset_password.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=f"Haslo musi miec co najmniej {MIN_PASSWORD_LENGTH} znakow.",
            token=token,
        )

    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        return render(
            request,
            "reset_password.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            error="Konto jest niedostepne.",
            token="",
        )

    user.password_hash = hasher.hash(password)
    row.used_at = datetime.now(UTC)
    db.commit()
    request.session["flash"] = "Haslo zmienione. Mozesz sie zalogowac."
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


def _find_valid_token(db, raw_token: str) -> PasswordResetToken | None:
    if not raw_token:
        return None
    row = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == _hash_token(raw_token))
    )
    if row is None or row.used_at is not None:
        return None
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires < datetime.now(UTC):
        return None
    return row
