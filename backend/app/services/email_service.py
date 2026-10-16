import hashlib
import hmac
import logging
import secrets
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)

EMAIL_LOG_FILE = settings.STORAGE_DIR / "email_outbox.log"


def generate_otp() -> str:
    """Generates a cryptographically secure 6-digit numeric one-time code."""
    return f"{secrets.randbelow(900000) + 100000}"


def hash_otp(email: str, otp: str) -> str:
    """OTPs are never stored in plain text; they are salted with the account email and the server secret."""
    return hashlib.sha256(f"{settings.SECRET_KEY}:{email.lower()}:{otp}".encode("utf-8")).hexdigest()


def otp_matches(email: str, otp: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(email, otp.strip()), stored_hash or "")


def smtp_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def send_otp_email(recipient_email: str, otp_code: str, user_name: str = "User", purpose: str = "reset") -> str:
    """
    Emails a one-time code through the configured SMTP server.

    Returns "sent", "not_configured" or "failed". When SMTP is not configured the
    code is written to storage/email_outbox.log so a developer can complete the flow
    locally; it is never claimed to have been delivered.
    """
    ttl = settings.OTP_TTL_MINUTES
    if purpose == "login":
        subject = "Your CapCheck AI sign-in code"
        intro = "Use this code to sign in to CapCheck AI:"
    else:
        subject = "Your CapCheck AI password reset code"
        intro = "Use this code to reset your CapCheck AI password:"

    html_content = f"""
    <div style="font-family:Inter,Arial,sans-serif;background:#f8f7f4;padding:24px;color:#0f1f3d">
      <div style="max-width:480px;margin:0 auto;background:#fff;border:1px solid #e3e1da;border-radius:8px;padding:28px">
        <div style="font-size:18px;font-weight:700;margin-bottom:16px">CapCheck AI</div>
        <p style="margin:0 0 8px">Hello {user_name},</p>
        <p style="margin:0 0 16px">{intro}</p>
        <div style="background:#f3f2ee;border:1px solid #e3e1da;border-radius:6px;padding:16px;text-align:center;
                    font-size:30px;font-weight:700;letter-spacing:8px;font-family:monospace">{otp_code}</div>
        <p style="margin:16px 0 0;font-size:14px">This code expires in {ttl} minutes and can be used once.
        If you did not request it, you can ignore this email; your account is unchanged.</p>
        <p style="margin:16px 0 0;font-size:12px;color:#6b7280">&copy; {datetime.utcnow().year} CapCheck AI</p>
      </div>
    </div>"""
    plain_content = (
        f"Hello {user_name},\n\n{intro} {otp_code}\n\n"
        f"The code expires in {ttl} minutes and can be used once. "
        f"If you did not request it, ignore this email.\n\nCapCheck AI"
    )

    if not smtp_configured():
        try:
            EMAIL_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(EMAIL_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.utcnow().isoformat()}] (NOT SENT - SMTP not configured) TO: {recipient_email} | CODE: {otp_code} | {subject}\n")
        except Exception as e:
            logger.warning(f"Could not append to email outbox log: {e}")
        logger.warning("SMTP is not configured; code for %s written to storage/email_outbox.log only.", recipient_email)
        return "not_configured"

    sender = settings.SMTP_FROM or settings.SMTP_USER
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"CapCheck AI <{sender}>"
        msg["To"] = recipient_email
        msg.attach(MIMEText(plain_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        if settings.SMTP_USE_SSL or settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15,
                                  context=ssl.create_default_context()) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(sender, [recipient_email], msg.as_string())
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(sender, [recipient_email], msg.as_string())
        logger.info("Delivered %s code to %s via SMTP.", purpose, recipient_email)
        return "sent"
    except Exception as err:
        logger.error("SMTP delivery to %s failed: %s", recipient_email, err)
        return "failed"
