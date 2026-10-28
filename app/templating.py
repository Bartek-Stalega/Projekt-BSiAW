from datetime import datetime
from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.config import APP_NAME, AUTHORS, ENVIRONMENT, GROUP_LABEL, TAGLINE
from app.markdown_render import render_markdown

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _format_datetime(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value else "-"


templates.env.filters["dt"] = _format_datetime
templates.env.filters["md"] = render_markdown


def render(request: Request, template: str, status_code: int = 200, **context):
    payload = {
        "app_name": APP_NAME,
        "tagline": TAGLINE,
        "group_label": GROUP_LABEL,
        "authors": AUTHORS,
        "environment": ENVIRONMENT,
        "current_user": getattr(request.state, "user", None),
        # Komunikat jednorazowy przekazywany po przekierowaniu.
        "flash": request.session.pop("flash", None),
    }
    payload.update(context)
    return templates.TemplateResponse(request, template, payload, status_code=status_code)
