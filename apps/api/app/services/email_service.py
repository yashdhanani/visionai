from __future__ import annotations

import logging
from typing import Optional

from app.config.settings import settings

logger = logging.getLogger("visionai.email")


def _send_mail(to: str, subject: str, body: str) -> bool:
    if not settings.EMAIL_ENABLED:
        logger.info(f"[EMAIL STUB] To: {to} | Subject: {subject}\n{body}")
        return True
    try:
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["From"] = settings.SMTP_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as exc:
        logger.error(f"Email send failed: {exc}")
        return False


def send_reset_email(email: str, token: str) -> bool:
    link = f"{settings.WEB_BASE_URL}/reset-password?token={token}"
    return _send_mail(
        email,
        "VisionAI — Password Reset",
        f"Click to reset your password: {link}\nToken: {token}\nExpires in 1 hour.",
    )


def send_verify_email(email: str, token: str) -> bool:
    link = f"{settings.WEB_BASE_URL}/verify-email?token={token}"
    return _send_mail(
        email,
        "VisionAI — Verify Your Email",
        f"Verify your email: {link}\nToken: {token}\nExpires in 24 hours.",
    )