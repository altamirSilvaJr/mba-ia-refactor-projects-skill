import os


def _as_bool(value):
    return value.lower() in {"1", "true", "yes", "on"}


class Settings:
    SECRET_KEY = os.getenv("APP_SECRET_KEY") or os.urandom(32).hex()
    DATABASE_PATH = os.getenv("APP_DATABASE_PATH", "loja.db")
    DEBUG = _as_bool(os.getenv("APP_DEBUG", "false"))
    HOST = os.getenv("APP_HOST", "127.0.0.1")
    PORT = int(os.getenv("APP_PORT", "5000"))
    CORS_ORIGINS = [origin.strip() for origin in os.getenv(
        "APP_CORS_ORIGINS", "http://localhost:3000"
    ).split(",") if origin.strip()]
    ADMIN_TOKEN = os.getenv("APP_ADMIN_TOKEN")
    SEED_ADMIN_PASSWORD = os.getenv("APP_SEED_ADMIN_PASSWORD")
    SEED_CUSTOMER_PASSWORD = os.getenv("APP_SEED_CUSTOMER_PASSWORD")
