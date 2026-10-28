"""Renderowanie tresci postow (Markdown -> bezpieczny HTML)."""

import bleach
import markdown as md_lib
from markupsafe import Markup

_ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "del",
    "s",
    "ul",
    "ol",
    "li",
    "a",
    "img",
    "blockquote",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "hr",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "input",
]


def _attr_filter(tag: str, name: str, value: str) -> bool:
    if tag == "a" and name in {"href", "title"}:
        return value.startswith(("http://", "https://", "/", "mailto:"))
    if tag == "img" and name == "src":
        return value.startswith("/uploads/")
    if tag == "img" and name in {"alt", "title"}:
        return True
    if tag in {"td", "th"} and name in {"align", "colspan", "rowspan"}:
        return True
    if tag == "input" and name in {"type", "checked", "disabled"}:
        # checkboxy z list zadan Toast UI
        return name != "type" or value == "checkbox"
    return False


def render_markdown(text: str | None) -> Markup:
    raw = (text or "").strip()
    if not raw:
        return Markup("")
    html = md_lib.markdown(
        raw,
        extensions=["nl2br", "sane_lists", "tables", "fenced_code"],
    )
    cleaned = bleach.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_attr_filter,
        strip=True,
    )
    return Markup(cleaned)
