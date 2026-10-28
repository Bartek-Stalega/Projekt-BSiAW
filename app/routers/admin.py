from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.deps import AdminDep, DbDep
from app.models import User
from app.templating import render

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("")
def admin_panel(request: Request, db: DbDep, admin: AdminDep):
    users = db.scalars(select(User).order_by(User.created_at.desc())).all()
    return render(request, "admin.html", users=users)


@router.post("/users/{user_id}/toggle-active")
def toggle_active(request: Request, db: DbDep, admin: AdminDep, user_id: int):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono uzytkownika")
    if user.id == admin.id:
        request.session["flash"] = "Nie mozesz dezaktywowac wlasnego konta."
        return RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)

    user.is_active = not user.is_active
    db.commit()
    state = "aktywne" if user.is_active else "zablokowane"
    request.session["flash"] = f"Konto {user.username} jest teraz {state}."
    return RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/{user_id}/toggle-admin")
def toggle_admin(request: Request, db: DbDep, admin: AdminDep, user_id: int):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono uzytkownika")
    if user.id == admin.id:
        request.session["flash"] = "Nie mozesz odebrac sobie uprawnien admina."
        return RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)

    user.is_admin = not user.is_admin
    db.commit()
    state = "adminem" if user.is_admin else "zwyklym uzytkownikiem"
    request.session["flash"] = f"{user.username} jest teraz {state}."
    return RedirectResponse("/admin", status_code=status.HTTP_303_SEE_OTHER)
