import os
from datetime import timedelta
from pathlib import Path


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me-before-deployment")
    DEBUG = os.getenv("FLASK_ENV") != "production"
    TEMPLATES_AUTO_RELOAD = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_REPORT_MB", "8")) * 1024 * 1024
    UPLOAD_FOLDER = str(Path(__file__).resolve().parent.parent / "instance" / "reports")
    DB_PATH = os.getenv("DB_PATH", str(Path(__file__).resolve().parent.parent / "instance" / "medtrack_db.json"))
    DATA_BACKEND = os.getenv("DATA_BACKEND", "persistent")
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "medtrack")
    S3_REPORTS_BUCKET = os.getenv("S3_REPORTS_BUCKET", "")
    SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")
    ALLOWED_REPORT_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
