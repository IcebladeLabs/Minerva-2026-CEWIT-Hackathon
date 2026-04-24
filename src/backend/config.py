import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-hackathon-key-change-in-production")
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "db", "app.db"))
TOKEN_EXPIRY_HOURS = int(os.environ.get("TOKEN_EXPIRY_HOURS", "24"))
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
DEBUG = os.environ.get("DEBUG", "1") == "1"

YOLO_MODEL = os.environ.get("YOLO_MODEL", "yolov8n.pt")
YOLO_CONFIDENCE = float(os.environ.get("YOLO_CONFIDENCE", "0.4"))

# SMS / Twilio
TWILIO_SID = os.environ.get("TWILIO_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER", "")
ALERT_PHONE_NUMBERS = [
    n.strip() for n in os.environ.get("ALERT_PHONES", "").split(",") if n.strip()
]
ALERT_COOLDOWN_SECONDS = int(os.environ.get("ALERT_COOLDOWN", "60"))

# Email / SMTP (stdlib — no extra deps)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
ALERT_EMAIL_TO = [
    e.strip() for e in os.environ.get("ALERT_EMAILS", "").split(",") if e.strip()
]

SNAPSHOTS_DIR = os.path.join(BASE_DIR, "snapshots")
