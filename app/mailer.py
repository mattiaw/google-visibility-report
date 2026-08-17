from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage


@dataclass(frozen=True)
class MailSettings:
    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str = "Google Visibility Report"
    use_tls: bool = True

    @classmethod
    def from_env(cls) -> "MailSettings":
        return cls(
            host=os.environ["GVR_SMTP_HOST"],
            port=int(os.environ.get("GVR_SMTP_PORT", "587")),
            username=os.environ["GVR_SMTP_USERNAME"],
            password=os.environ["GVR_SMTP_PASSWORD"],
            from_email=os.environ["GVR_SMTP_FROM_EMAIL"],
            from_name=os.environ.get("GVR_SMTP_FROM_NAME", "Google Visibility Report"),
            use_tls=os.environ.get("GVR_SMTP_USE_TLS", "1") not in {"0", "false", "False"},
        )


def send_report_email(settings: MailSettings, to_email: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.from_name} <{settings.from_email}>"
    message["To"] = to_email
    message.set_content(body)

    with smtplib.SMTP(settings.host, settings.port, timeout=30) as smtp:
        if settings.use_tls:
            smtp.starttls()
        smtp.login(settings.username, settings.password)
        smtp.send_message(message)

