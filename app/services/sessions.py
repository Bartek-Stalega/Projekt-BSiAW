import logging
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.models import User, UserSession, utcnow
from app.security import generate_token, hash_token

settings = get_settings()
logger = logging.getLogger("secforum.sessions")


def create_session(
    db: DbSession, user: User, ip_address: str | None, user_agent: str | None
) -> tuple[UserSession, str]:
    """Tworzy nowa sesje i zwraca (rekord, surowy token do ciasteczka)."""
    token = generate_token()
    record = UserSession(
        token_hash=hash_token(token),
        user_id=user.id,
        expires_at=utcnow() + timedelta(minutes=settings.session_absolute_ttl_minutes),
        ip_address=ip_address,
        user_agent=(user_agent or "")[:255] or None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, token


def get_valid_session(db: DbSession, token: str | None) -> UserSession | None:
    """Zwraca aktywna sesje i odswieza ``last_seen_at`` (kontrola bezczynnosci)."""
    if not token:
        return None
    record = db.scalar(select(UserSession).where(UserSession.token_hash == hash_token(token)))
    if record is None or record.revoked_at is not None:
        return None

    now = utcnow()
    if record.expires_at <= now:
        revoke_session(db, record, reason="expired")
        return None

    idle_limit = timedelta(minutes=settings.session_idle_timeout_minutes)
    if now - record.last_seen_at > idle_limit:
        revoke_session(db, record, reason="idle_timeout")
        return None

    record.last_seen_at = now
    db.commit()
    return record


def revoke_session(db: DbSession, record: UserSession, reason: str = "logout") -> None:
    if record.revoked_at is None:
        record.revoked_at = utcnow()
        db.commit()
        logger.info(
            "session_revoked session_id=%s user_id=%s reason=%s", record.id, record.user_id, reason
        )


def revoke_other_sessions(db: DbSession, user_id: int, keep_session_id: int) -> int:
    result = db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.id != keep_session_id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=utcnow())
    )
    db.commit()
    return result.rowcount or 0


def list_sessions(db: DbSession, user_id: int) -> list[UserSession]:
    return list(
        db.scalars(
            select(UserSession)
            .where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
            .order_by(UserSession.last_seen_at.desc())
        )
    )


def purge_expired(db: DbSession) -> int:
    """Sprzatanie wygaslych sesji - wolane przy starcie aplikacji."""
    result = db.execute(
        update(UserSession)
        .where(UserSession.expires_at <= utcnow(), UserSession.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    db.commit()
    return result.rowcount or 0
