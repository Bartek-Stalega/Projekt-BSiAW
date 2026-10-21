from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.config import MIN_PASSWORD_LENGTH
from app.deps import DbDep, UserDep
from app.models import User
from app.templating import render

router = APIRouter(tags=["auth"])
hasher = PasswordHasher()


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
    password: Annotated[str, Form()],
):
    username = username.strip()

    error = None
    if not 3 <= len(username) <= 32:
        error = "Nazwa uzytkownika musi miec od 3 do 32 znakow."
    elif len(password) < MIN_PASSWORD_LENGTH:
        error = f"Haslo musi miec co najmniej {MIN_PASSWORD_LENGTH} znakow."
    elif db.scalar(select(User).where(User.username == username)):
        error = "Taka nazwa uzytkownika jest juz zajeta."

    if error:
        return render(
            request,
            "register.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=error,
            username=username,
        )

    db.add(User(username=username, password_hash=hasher.hash(password)))
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
        if user is None:
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
