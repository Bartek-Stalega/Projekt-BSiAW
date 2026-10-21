from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.dependencies import CsrfDep, CurrentUserDep, DbDep, OptionalUserDep
from app.models import Post, Thread
from app.web import render

router = APIRouter(tags=["forum"])
settings = get_settings()


def _thread_list(db, limit: int, offset: int = 0):
    reply_counts = dict(
        db.execute(select(Post.thread_id, func.count(Post.id)).group_by(Post.thread_id)).all()
    )
    threads = list(
        db.scalars(
            select(Thread)
            .options(selectinload(Thread.author))
            .order_by(Thread.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return [(thread, reply_counts.get(thread.id, 0)) for thread in threads]


@router.get("/")
def index(request: Request, db: DbDep, user: OptionalUserDep):
    items = _thread_list(db, limit=settings.page_size)
    return render(request, "index.html", {"threads": items})


@router.get("/threads/new")
def new_thread_form(request: Request, user: CurrentUserDep):
    return render(request, "new_thread.html")


@router.post("/threads/new")
def create_thread(
    request: Request,
    db: DbDep,
    _csrf: CsrfDep,
    user: CurrentUserDep,
    title: Annotated[str, Form()],
    body: Annotated[str, Form()],
):
    title = title.strip()
    body = body.strip()

    error = None
    if len(title) < 5 or len(title) > settings.max_thread_title_length:
        error = f"Tytul musi miec od 5 do {settings.max_thread_title_length} znakow."
    elif len(body) < 5 or len(body) > settings.max_post_body_length:
        error = f"Tresc musi miec od 5 do {settings.max_post_body_length} znakow."

    if error:
        return render(
            request,
            "new_thread.html",
            {"error": error, "form": {"title": title, "body": body}},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    thread = Thread(title=title, author_id=user.id)
    db.add(thread)
    db.flush()
    db.add(Post(thread_id=thread.id, author_id=user.id, body=body))
    db.commit()
    return RedirectResponse(
        f"/threads/{thread.id}?msg=thread_created", status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/threads/{thread_id}")
def thread_detail(request: Request, db: DbDep, user: OptionalUserDep, thread_id: int):
    thread = db.scalar(
        select(Thread)
        .options(selectinload(Thread.author), selectinload(Thread.posts).selectinload(Post.author))
        .where(Thread.id == thread_id)
    )
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono watku")
    return render(request, "thread.html", {"thread": thread})


@router.post("/threads/{thread_id}/posts")
def create_post(
    request: Request,
    db: DbDep,
    _csrf: CsrfDep,
    user: CurrentUserDep,
    thread_id: int,
    body: Annotated[str, Form()],
):
    thread = db.get(Thread, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono watku")

    body = body.strip()
    if len(body) < 2 or len(body) > settings.max_post_body_length:
        return render(
            request,
            "thread.html",
            {
                "thread": thread,
                "error": f"Odpowiedz musi miec od 2 do {settings.max_post_body_length} znakow.",
                "form": {"body": body},
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    db.add(Post(thread_id=thread.id, author_id=user.id, body=body))
    db.commit()
    return RedirectResponse(
        f"/threads/{thread.id}?msg=post_created#ostatni", status_code=status.HTTP_303_SEE_OTHER
    )
