import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise ValueError(
            "SECRET_KEY bulunamadı. .env dosyasını kontrol et."
        )

    AGENT_AUTH_TOKEN = os.getenv(
        "AGENT_AUTH_TOKEN",
        ""
    ).strip()

    if not AGENT_AUTH_TOKEN:
        raise ValueError(
            "AGENT_AUTH_TOKEN bulunamadı. "
            ".env dosyasını kontrol et."
        )

    DB_HOST = os.getenv(
        "DB_HOST",
        "localhost"
    )

    DB_USER = os.getenv(
        "DB_USER",
        "root"
    )

    DB_PASSWORD = os.getenv(
        "DB_PASSWORD",
        ""
    )

    DB_NAME = os.getenv(
        "DB_NAME",
        "remote_vm_management"
    )

    TURNSTILE_SITE_KEY = os.getenv(
        "TURNSTILE_SITE_KEY",
        ""
    )

    TURNSTILE_SECRET_KEY = os.getenv(
        "TURNSTILE_SECRET_KEY",
        ""
    )

    TURNSTILE_VERIFY_URL = (
        "https://challenges.cloudflare.com/"
        "turnstile/v0/siteverify"
    )

    if (
        not TURNSTILE_SITE_KEY
        or not TURNSTILE_SECRET_KEY
    ):
        raise ValueError(
            "Turnstile anahtarları bulunamadı. "
            ".env dosyasını kontrol et."
        )

    SESSION_COOKIE_NAME = "remote_vm_session"

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = "Lax"

    SESSION_COOKIE_SECURE = (
        os.getenv(
            "SESSION_COOKIE_SECURE",
            "false"
        ).lower() == "true"
    )

    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(
            os.getenv(
                "SESSION_LIFETIME_MINUTES",
                "30"
            )
        )
    )