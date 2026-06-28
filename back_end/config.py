import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'database' / 'medochat.sqlite3').as_posix()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE", False)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = _bool_env("REMEMBER_COOKIE_SECURE", False)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    SOCKETIO_CORS_ORIGINS = os.getenv("SOCKETIO_CORS_ORIGINS", "*")
    MEDO_AI_PROVIDER = os.getenv("MEDO_AI_PROVIDER", "disabled")
    MEDO_AI_API_KEY = os.getenv("MEDO_AI_API_KEY", "")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE", True)
    REMEMBER_COOKIE_SECURE = _bool_env("REMEMBER_COOKIE_SECURE", True)


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


def get_config(config_name=None):
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    return configs.get(config_name, DevelopmentConfig)
