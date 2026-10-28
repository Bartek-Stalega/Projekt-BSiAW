"""Wysylka maili przez SMTP (w DEV: Mailhog)."""

import logging
import smtplib
from email.message import EmailMessage

from app.config import APP_NAME, PUBLIC_BASE_URL, SMTP_FROM, SMTP_HOST, SMTP_PORT

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            smtp.send_message(message)
    except OSError:
        logger.exception("Nie udalo sie wyslac maila do %s", to)
        raise


def send_password_reset(to: str, raw_token: str) -> None:
    link = f"{PUBLIC_BASE_URL}/reset-password?token={raw_token}"
    body = (
        f"Witaj w {APP_NAME}.\n\n"
        f"Ktos poprosil o reset hasla. Kliknij link (wazny 1 godzine):\n\n"
        f"{link}\n\n"
        f"Jesli to nie Ty - zignoruj te wiadomosc.\n"
    )
    send_email(to, f"{APP_NAME} - reset hasla", body)
