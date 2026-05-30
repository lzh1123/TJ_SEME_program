import smtplib
from email.message import EmailMessage

from app.core.config import get_settings


class EmailService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def send_verify_code(self, email: str, purpose: str, code: str) -> None:
        if not self.settings.smtp_enabled:
            return
        if not self.settings.smtp_host or not self.settings.smtp_user:
            return

        msg = EmailMessage()
        msg["Subject"] = f"[{self.settings.app_name}] Verification code"
        msg["From"] = self.settings.smtp_user
        msg["To"] = email
        msg.set_content(
            f"Your verification code for {purpose} is {code}. "
            f"It will expire in 10 minutes."
        )

        if self.settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(
                self.settings.smtp_host, self.settings.smtp_ssl_port, timeout=10
            ) as server:
                server.login(self.settings.smtp_user, self.settings.smtp_password)
                server.send_message(msg)
            return

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_starttls_port, timeout=10) as server:
            server.starttls()
            server.login(self.settings.smtp_user, self.settings.smtp_password)
            server.send_message(msg)
