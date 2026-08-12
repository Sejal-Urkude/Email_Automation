import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    # Email Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    FROM_EMAIL = os.getenv('FROM_EMAIL', '')
    FROM_NAME = os.getenv('FROM_NAME', 'VASPP GmbH')

    # Webinar Details
    WEBINAR_DATE = os.getenv('WEBINAR_DATE', '2026-09-15')
    WEBINAR_TIME = os.getenv('WEBINAR_TIME', '11:00')
    WEBINAR_TIMEZONE = os.getenv('WEBINAR_TIMEZONE', 'CET')
    WEBINAR_DURATION = int(os.getenv('WEBINAR_DURATION', 45))
    REGISTER_LINK = os.getenv('REGISTER_LINK', '#')
    JOIN_LINK = os.getenv('JOIN_LINK', '#')
    RECORDING_LINK = os.getenv('RECORDING_LINK', '#')
    BOOKING_LINK = os.getenv('BOOKING_LINK', '#')

    # Server
    PORT = int(os.getenv('PORT', 3000))
    EMAIL_SEND_HOUR = int(os.getenv('EMAIL_SEND_HOUR', 10))
    EMAIL_SEND_MINUTE = int(os.getenv('EMAIL_SEND_MINUTE', 0))

    # Paths
    TEMPLATES_DIR = BASE_DIR / 'templates'
    DATA_DIR = BASE_DIR / 'data'
    LOGS_DIR = BASE_DIR / 'logs'
    PUBLIC_DIR = BASE_DIR / 'public'

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        for directory in [cls.DATA_DIR, cls.LOGS_DIR, cls.PUBLIC_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

config = Config()