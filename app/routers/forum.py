from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import MAX_BODY_LENGTH, MAX_TITLE_LENGTH
from app.deps import AdminDep, DbDep, LoggedInDep, UserDep
from app.models import Post, Thread
from app.templating import render
from app.uploads import UploadError, save_image

router = APIRouter(tags=["forum"])


@router.get("/")
def index(request: Request, db: DbDep, user: UserDep):
    threads = db.scalars(
        select(Thread)
        .options(
            selectinload(Thread.author),
            selectinload(Thread.posts).selectinload(Post.author),
        )
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


@router.post("/api/uploads")
async def api_upload_image(user: LoggedInDep, image: Annotated[UploadFile, File()]):
    """Wgrywa obraz i zwraca URL do wstawienia w Markdown (![](/uploads/...))."""
    try:
        name = save_image(image)
    except UploadError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=status.HTTP_400_BAD_REQUEST)
    if not name:
        return JSONResponse({"detail": "Brak pliku."}, status_code=status.HTTP_400_BAD_REQUEST)
    return {"url": f"/uploads/{name}"}


@router.post("/threads/{thread_id}/delete")
def delete_thread(request: Request, db: DbDep, admin: AdminDep, thread_id: int):
    thread = db.get(Thread, thread_id)
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono watku")
    db.delete(thread)
    db.commit()
    request.session["flash"] = "Watek usuniety."
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/posts/{post_id}/delete")
def delete_post(request: Request, db: DbDep, admin: AdminDep, post_id: int):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono wpisu")
    thread_id = post.thread_id
    post_count = len(db.scalars(select(Post).where(Post.thread_id == thread_id)).all())
    if post_count <= 1:
        thread = db.get(Thread, thread_id)
        if thread:
            db.delete(thread)
        db.commit()
        request.session["flash"] = "Watek usuniety (ostatni wpis)."
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    db.delete(post)
    db.commit()
    request.session["flash"] = "Wpis usuniety."
    return RedirectResponse(f"/threads/{thread_id}", status_code=status.HTTP_303_SEE_OTHER)
