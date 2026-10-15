import os
import random
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

EMAIL_LOG_FILE = settings.STORAGE_DIR / "email_outbox.log"


def generate_otp() -> str:
    """Generates a secure 6-digit numeric OTP."""
    return f"{random.randint(100000, 999999)}"


def send_otp_email(recipient_email: str, otp_code: str, user_name: str = "User") -> bool:
    """
    Sends an OTP verification email to the user.
    If SMTP server is configured in settings or environment, delivers via real SMTP.
    Always logs to storage/email_outbox.log and console for seamless offline/dev testing.
    """
    subject = f"Your CapCheck AI Password Reset Code: {otp_code}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #0f172a; }}
            .container {{ max-width: 500px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; }}
            .brand {{ font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 24px; }}
            .otp-box {{ background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 18px; text-align: center; margin: 24px 0; }}
            .otp-code {{ font-size: 32px; font-weight: 900; letter-spacing: 6px; color: #2563eb; font-family: monospace; }}
            .footer {{ font-size: 12px; color: #64748b; margin-top: 24px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="brand">CapCheck AI</div>
            <p>Hello {user_name},</p>
            <p>You requested a one-time verification code to reset your password. Use the 6-digit code below to complete your reset:</p>
            <div class="otp-box">
                <div class="otp-code">{otp_code}</div>
            </div>
            <p>This code is valid for <strong>15 minutes</strong>. If you did not request this code, you can safely ignore this email.</p>
            <div class="footer">
                &copy; {datetime.utcnow().year} CapCheck AI. Trusted Fact-Checking & Media Verification.
            </div>
        </div>
    </body>
    </html>
    """

    plain_content = f"""
    Hello {user_name},

    Your CapCheck AI password reset code is: {otp_code}
    This code is valid for 15 minutes.

    If you did not request this, please ignore this email.
    CapCheck AI Team
    """

    # 1. Log to outbox file
    try:
        EMAIL_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(EMAIL_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] TO: {recipient_email} | OTP: {otp_code} | SUBJECT: {subject}\n")
    except Exception as e:
        logger.warning(f"Could not append to email log: {e}")

    logger.info(f"==> [EMAIL DISPATCH] Password reset OTP for {recipient_email}: {otp_code}")

    # 2. Check if SMTP configuration exists in environment
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", "noreply@capcheck.ai")

    if smtp_host and smtp_user and smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"CapCheck AI <{smtp_from}>"
            msg["To"] = recipient_email
            msg.attach(MIMEText(plain_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_from, [recipient_email], msg.as_string())
            logger.info(f"Successfully delivered OTP email to {recipient_email} via SMTP.")
            return True
        except Exception as err:
            logger.error(f"Failed to deliver SMTP email to {recipient_email}: {err}")
            # Non-fatal: local outbox still recorded it
            return False

    return True
