"""
Alert system — SMS via Twilio + Email via SMTP (stdlib).
Rate-limited per anomaly type to avoid spamming operators.
Falls back to local logging when neither is configured.
"""
from __future__ import annotations
import time, logging, threading, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import (
    TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER,
    ALERT_PHONE_NUMBERS, ALERT_COOLDOWN_SECONDS,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO,
)
from backend import database as db

log = logging.getLogger(__name__)

# ── Twilio (optional) ──
try:
    from twilio.rest import Client as TwilioClient
    _twilio: TwilioClient | None = None
    if TWILIO_SID and TWILIO_AUTH_TOKEN:
        _twilio = TwilioClient(TWILIO_SID, TWILIO_AUTH_TOKEN)
except ImportError:
    _twilio = None
    log.info("Twilio not installed — SMS disabled")

# ── Rate-limiting ──
_cooldowns: dict[str, float] = {}
_cooldown_lock = threading.Lock()

SEVERITY_EMOJI = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}

_email_configured = bool(SMTP_USER and SMTP_PASSWORD and ALERT_EMAIL_TO)


def _can_send(anomaly_key: str) -> bool:
    now = time.time()
    with _cooldown_lock:
        last = _cooldowns.get(anomaly_key, 0)
        if now - last < ALERT_COOLDOWN_SECONDS:
            return False
        _cooldowns[anomaly_key] = now
        return True


def _send_email(subject: str, body: str):
    """Send alert email via SMTP. Runs in its own thread to avoid blocking."""
    if not _email_configured:
        return
    def _do():
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = ", ".join(ALERT_EMAIL_TO)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as srv:
                srv.starttls()
                srv.login(SMTP_USER, SMTP_PASSWORD)
                srv.sendmail(SMTP_USER, ALERT_EMAIL_TO, msg.as_string())
            log.info("Email sent to %s", ALERT_EMAIL_TO)
        except Exception as e:
            log.error("Email failed: %s", e)
    threading.Thread(target=_do, daemon=True).start()


def _send_sms(body: str):
    if not (_twilio and TWILIO_FROM_NUMBER and ALERT_PHONE_NUMBERS):
        return
    for phone in ALERT_PHONE_NUMBERS:
        try:
            _twilio.messages.create(body=body, from_=TWILIO_FROM_NUMBER, to=phone)
            log.info("SMS sent to %s", phone)
        except Exception as e:
            log.error("SMS failed to %s: %s", phone, e)


def send_alert(
    anomaly_type: str,
    severity: str,
    feed_name: str,
    class_name: str,
    confidence: float,
    snapshot_file: str = "",
) -> bool:
    cooldown_key = f"{anomaly_type}:{feed_name}"
    if not _can_send(cooldown_key):
        return False

    emoji = SEVERITY_EMOJI.get(severity, "")
    msg = (
        f"{emoji} {severity.upper()} ALERT\n"
        f"Type: {anomaly_type}\n"
        f"Camera: {feed_name}\n"
        f"Detected: {class_name} ({confidence:.0%})\n"
        f"Time: {time.strftime('%H:%M:%S')}"
    )

    db.execute(
        "INSERT INTO alerts (anomaly_type, severity, feed_name, class_name, confidence, message, snapshot) "
        "VALUES (?,?,?,?,?,?,?)",
        (anomaly_type, severity, feed_name, class_name, confidence, msg, snapshot_file),
    )

    _send_sms(msg)
    _send_email(
        subject=f"[Minerva] {severity.upper()}: {anomaly_type} on {feed_name}",
        body=msg,
    )

    if not _twilio and not _email_configured:
        log.info("Alert (local-only): %s", msg.replace("\n", " | "))

    return True


def get_recent_alerts(limit: int = 50) -> list[dict]:
    rows = db.query(
        "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    return [dict(r) for r in rows]
