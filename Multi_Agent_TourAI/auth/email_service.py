import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from Multi_Agent_TourAI.utils import get_logger

logger = get_logger("Multi_Agent_TourAI.auth.email_service")


def get_smtp_config():
    """Retrieves SMTP configuration from environment variables."""
    # Sanitize password: strip whitespace and internal spaces (e.g. Gmail 16-char app password format 'xxxx xxxx xxxx xxxx')
    raw_password = os.getenv("SMTP_PASSWORD", "").strip()
    clean_password = raw_password.replace(" ", "")

    return {
        "host": os.getenv("SMTP_HOST", "smtp.gmail.com" if "gmail.com" in os.getenv("SMTP_USER", "") else "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", "").strip(),
        "password": clean_password,
        "from_email": os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USER", "noreply@tourai.com")).strip(),
        "from_name": os.getenv("SMTP_FROM_NAME", "TourAI").strip(),
        "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes"),
    }


def is_smtp_configured() -> bool:
    """Returns True if minimum required SMTP credentials are provided."""
    config = get_smtp_config()
    return bool(config["host"] and config["port"])


def build_password_reset_email_html(otp: str) -> str:
    """Builds a responsive, branded HTML email template for OTP password reset."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Password Reset Code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #05070a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #e2e8f0;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #05070a; padding: 40px 10px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width: 520px; background-color: #0a0d14; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; overflow: hidden; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);">
          <!-- Header -->
          <tr>
            <td style="padding: 32px 36px 20px; border-bottom: 1px solid rgba(255, 255, 255, 0.06); text-align: center;">
              <!-- Brand Logo: Exact Match to App Sidebar/Navbar (Pure HTML/CSS - Never blocked by email clients) -->
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: 0 auto 16px auto; display: inline-table; vertical-align: middle;">
                <tr>
                  <td style="vertical-align: middle; padding-right: 10px;">
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="width: 32px; height: 32px; background-color: #ffffff; border-radius: 8px;">
                      <tr>
                        <td align="center" valign="middle" style="width: 32px; height: 32px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 15px; font-weight: 900; color: #000000; letter-spacing: -1px; line-height: 32px; text-align: center;">
                          .\\\\
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td style="vertical-align: middle; text-align: left;">
                    <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; line-height: 32px;">TourAI<span style="color: #2dd4bf;">.ai</span></span>
                  </td>
                </tr>
              </table>
              <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #ffffff;">Password Reset Verification</h1>
            </td>
          </tr>
          <!-- Body Content -->
          <tr>
            <td style="padding: 32px 36px;">
              <p style="margin: 0 0 16px; font-size: 14px; line-height: 1.6; color: #94a3b8;">Hello,</p>
              <p style="margin: 0 0 24px; font-size: 14px; line-height: 1.6; color: #cbd5e1;">
                We received a request to reset your TourAI account password. Use the verification code below to complete your reset request:
              </p>
              
              <!-- OTP Box -->
              <div style="background-color: #111622; border: 1px solid rgba(20, 184, 166, 0.3); border-radius: 12px; padding: 20px; text-align: center; margin: 24px 0;">
                <span style="display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8; margin-bottom: 8px;">Your 6-Digit Code</span>
                <span style="font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace; font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #2dd4bf;">{otp}</span>
              </div>

              <p style="margin: 0 0 12px; font-size: 13px; line-height: 1.6; color: #f59e0b; font-weight: 500;">
                &#9888; This code expires in <strong>5 minutes</strong>. Do not share it with anyone.
              </p>
              <p style="margin: 0 0 24px; font-size: 13px; line-height: 1.6; color: #64748b;">
                If you did not request this password reset, you can safely ignore this email. Your current password remains secure.
              </p>
              <p style="margin: 0; font-size: 13px; color: #94a3b8;">
                Best regards,<br>
                <strong style="color: #cbd5e1;">TourAI Team</strong>
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="padding: 20px 36px; background-color: #07090e; border-top: 1px solid rgba(255, 255, 255, 0.04); text-align: center;">
              <p style="margin: 0; font-size: 11px; color: #475569;">
                &copy; 2026 TourAI. Multi-Agent AI System. All rights reserved. Automated message, do not reply.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def build_password_reset_email_text(otp: str) -> str:
    """Builds standard plain text email body."""
    return f"""Hello,

We received a request to reset your Multi-Agent-TourAI account password.

Your verification code is:

{otp}

This code expires in 5 minutes. Do not share it with anyone.

If you did not request this password reset, you can safely ignore this email.

TourAI Team
"""


def send_password_reset_email(to_email: str, otp: str) -> bool:
    """
    Sends a password reset verification code to the recipient email address.
    
    Security:
    - Never logs plain credentials.
    - Uses STARTTLS encryption where supported.
    - In development mode (if SMTP is not configured), logs a safe simulation notice.
    - Handles network and authentication exceptions without crashing.
    """
    config = get_smtp_config()
    to_email_clean = to_email.strip().lower()

    if not is_smtp_configured():
        logger.warning(
            f"[EMAIL] SMTP is not configured. Simulating delivery to {to_email_clean} "
            f"(Configure SMTP_HOST and SMTP_PORT to send real emails)."
        )
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "TourAI – Password Reset Verification"
        msg["From"] = f"{config['from_name']} <{config['from_email']}>"
        msg["To"] = to_email_clean

        part_text = MIMEText(build_password_reset_email_text(otp), "plain", "utf-8")
        part_html = MIMEText(build_password_reset_email_html(otp), "html", "utf-8")

        msg.attach(part_text)
        msg.attach(part_html)

        if config["port"] == 465:
            # SSL directly
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(config["host"], config["port"], context=context, timeout=10.0) as server:
                if config["user"] and config["password"]:
                    server.login(config["user"], config["password"])
                server.sendmail(config["from_email"], [to_email_clean], msg.as_string())
        else:
            # Standard SMTP with STARTTLS
            with smtplib.SMTP(config["host"], config["port"], timeout=10.0) as server:
                if config["use_tls"]:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                if config["user"] and config["password"]:
                    server.login(config["user"], config["password"])
                server.sendmail(config["from_email"], [to_email_clean], msg.as_string())

        logger.info(f"[EMAIL] Password reset code successfully sent to {to_email_clean}")
        return True
    except smtplib.SMTPException as se:
        logger.error(f"[EMAIL] SMTP delivery failed to {to_email_clean}: {se}")
        return False
    except Exception as e:
        logger.error(f"[EMAIL] Unexpected error sending email to {to_email_clean}: {e}", exc_info=True)
        return False


__all__ = [
    "send_password_reset_email",
    "is_smtp_configured",
    "get_smtp_config",
    "build_password_reset_email_html",
    "build_password_reset_email_text",
]
