from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from app.db import get_db
from app.models import User

DbDep = Annotated[DbSession, Depends(get_db)]


def current_user(request: Request, db: DbDep) -> User | None:
    """Uzytkownik z sesji (w ciasteczku jest tylko podpisane ``user_id``)."""
    user_id = request.session.get("user_id")
    user = db.get(User, user_id) if user_id else None
    if user is not None and not user.is_active:
        request.session.clear()
        user = None
    request.state.user = user
    return user


UserDep = Annotated[User | None, Depends(current_user)]


def require_login(user: UserDep) -> User:
    if user is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user


LoggedInDep = Annotated[User, Depends(require_login)]


def require_admin(user: LoggedInDep) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Wymagane konto administratora.")
    return user


AdminDep = Annotated[User, Depends(require_admin)]
