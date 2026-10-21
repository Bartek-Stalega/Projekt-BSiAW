from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import MAX_BODY_LENGTH, MAX_TITLE_LENGTH
from app.deps import DbDep, LoggedInDep, UserDep
from app.models import Post, Thread
from app.templating import render

router = APIRouter(tags=["forum"])


@router.get("/")
def index(request: Request, db: DbDep, user: UserDep):
    threads = db.scalars(
        select(Thread)
        .options(selectinload(Thread.author), selectinload(Thread.posts))
        .order_by(Thread.created_at.desc())
    ).all()
    return render(request, "index.html", threads=threads)


@router.get("/threads/new")
def new_thread_form(request: Request, user: LoggedInDep):
    return render(request, "new_thread.html")


@router.post("/threads/new")
def create_thread(
    request: Request,
    db: DbDep,
    user: LoggedInDep,
    title: Annotated[str, Form()],
    body: Annotated[str, Form()],
):
    title, body = title.strip(), body.strip()

    if not 5 <= len(title) <= MAX_TITLE_LENGTH or not 5 <= len(body) <= MAX_BODY_LENGTH:
        return render(
            request,
            "new_thread.html",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=f"Tytul: 5-{MAX_TITLE_LENGTH} znakow, tresc: 5-{MAX_BODY_LENGTH} znakow.",
            title=title,
            body=body,
        )

    thread = Thread(title=title, author_id=user.id)
    db.add(thread)
    db.flush()
    db.add(Post(thread_id=thread.id, author_id=user.id, body=body))
    db.commit()
    return RedirectResponse(f"/threads/{thread.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/threads/{thread_id}")
def thread_detail(request: Request, db: DbDep, user: UserDep, thread_id: int):
    thread = db.scalar(
        select(Thread)
        .options(selectinload(Thread.author), selectinload(Thread.posts).selectinload(Post.author))
        .where(Thread.id == thread_id)
    )
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono watku")
    return render(request, "thread.html", thread=thread)


@router.post("/threads/{thread_id}/posts")
def create_post(
    request: Request,
    db: DbDep,
    user: LoggedInDep,
    thread_id: int,
    body: Annotated[str, Form()],
):
    thread = db.get(Thread, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono watku")

    body = body.strip()
    if not 2 <= len(body) <= MAX_BODY_LENGTH:
        request.session["flash"] = "Odpowiedz nie moze byc pusta."
        return RedirectResponse(f"/threads/{thread_id}", status_code=status.HTTP_303_SEE_OTHER)

    db.add(Post(thread_id=thread.id, author_id=user.id, body=body))
    db.commit()
    return RedirectResponse(f"/threads/{thread_id}", status_code=status.HTTP_303_SEE_OTHER)
