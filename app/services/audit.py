import logging

from sqlalchemy.orm import Session as DbSession

from app.models import AuditLog

logger = logging.getLogger("secforum.audit")


def record(
    db: DbSession,
    event: str,
    username: str | None = None,
    ip_address: str | None = None,
    detail: str | None = None,
) -> None:
    """Zapisuje zdarzenie bezpieczenstwa do bazy i do logu aplikacji."""
    db.add(
        AuditLog(
            event=event,
            username=(username or "")[:64] or None,
            ip_address=ip_address,
            detail=(detail or "")[:255] or None,
        )
    )
    db.commit()
    logger.info("audit event=%s user=%s ip=%s detail=%s", event, username, ip_address, detail)
