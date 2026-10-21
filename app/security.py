import hashlib
import hmac
import re
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

# Argon2id - rekomendacja OWASP Password Storage Cheat Sheet.
_hasher = PasswordHasher(time_cost=2, memory_cost=64 * 1024, parallelism=2)

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
MIN_PASSWORD_LENGTH = 10


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError, ValueError):
        return False


def needs_rehash(password_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(password_hash)
    except (InvalidHashError, ValueError):
        return True


def generate_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """Token sesji trafia do bazy wylacznie jako skrot (jak hasla w /etc/shadow)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def tokens_match(expected: str | None, provided: str | None) -> bool:
    if not expected or not provided:
        return False
    return hmac.compare_digest(expected, provided)


def validate_registration(
    username: str, email: str, password: str, password_confirm: str
) -> str | None:
    """Zwraca komunikat bledu albo None, gdy dane sa poprawne."""
    if not USERNAME_RE.match(username):
        return "Nazwa uzytkownika: 3-32 znaki, dozwolone litery, cyfry oraz . _ -"
    if not EMAIL_RE.match(email) or len(email) > 255:
        return "Podaj poprawny adres e-mail."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Haslo musi miec co najmniej {MIN_PASSWORD_LENGTH} znakow."
    if len(password) > 128:
        return "Haslo moze miec maksymalnie 128 znakow."
    if password != password_confirm:
        return "Hasla nie sa identyczne."
    if password.lower() in {"password12", "haslo12345", "qwerty1234", "1234567890"}:
        return "To haslo jest zbyt popularne."
    return None
