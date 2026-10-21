from datetime import UTC, datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, TypeDecorator, func
from sqlalchemy import DateTime as SaDateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class DateTime(TypeDecorator):
    """Znacznik czasu zawsze w UTC i zawsze swiadomy strefy.

    PostgreSQL przechowuje strefe, SQLite nie - ten typ wyrownuje zachowanie,
    dzieki czemu porownania dat dzialaja tak samo w obu bazach.
    """

    impl = SaDateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    threads: Mapped[list["Thread"]] = relationship(back_populates="author")
    posts: Mapped[list["Post"]] = relationship(back_populates="author")
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserSession(Base):
    """Sesja trzymana po stronie serwera.

    W ciasteczku ladu je tylko losowy token; w bazie jego skrot. Dzieki temu
    aplikacja jest bezstanowa i mozna ja skalowac horyzontalnie za load
    balancerem bez sticky sessions (wymaganie L3).
    """

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45), default=None)
    user_agent: Mapped[str | None] = mapped_column(String(255), default=None)

    user: Mapped[User] = relationship(back_populates="sessions")

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > utcnow()


class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    author: Mapped[User] = relationship(back_populates="threads")
    posts: Mapped[list["Post"]] = relationship(
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="Post.created_at",
    )


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    thread_id: Mapped[int] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, server_default=func.now()
    )

    thread: Mapped[Thread] = relationship(back_populates="posts")
    author: Mapped[User] = relationship(back_populates="posts")


class AuditLog(Base):
    """Minimalny log zdarzen bezpieczenstwa (logowania, wylogowania, rejestracje).

    Na L7 bedzie zrodlem dla monitoringu sesji / alertow w Azure Monitor.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str] = mapped_column(String(48), index=True)
    username: Mapped[str | None] = mapped_column(String(64), default=None)
    ip_address: Mapped[str | None] = mapped_column(String(45), default=None)
    detail: Mapped[str | None] = mapped_column(String(255), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
