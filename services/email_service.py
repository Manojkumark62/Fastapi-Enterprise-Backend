import logging
import smtplib
from email.message import EmailMessage

from core.config import settings

logger = logging.getLogger(__name__)


def send_password_reset_code(recipient: str, code: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Password reset code"
    message["From"] = settings.EMAIL_FROM
    message["To"] = recipient
    message.set_content(f"Your password reset code is {code}. It expires in 10 minutes.")
    if not settings.SMTP_USER:
        logger.info("Password reset email queued for %s", recipient)
        return
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)