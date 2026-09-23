"""Environment-driven configuration. Never hardcode secrets here."""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()  # reads .env in the project root when present


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _as_int(value: str | None, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return default


@dataclass
class Settings:
    db_server: str = field(default_factory=lambda: os.getenv("DB_SERVER", "127.0.0.1"))
    db_database: str = field(default_factory=lambda: os.getenv("DB_DATABASE", "PhonebookDb"))
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", ""))
    db_password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    db_port: int = field(default_factory=lambda: _as_int(os.getenv("DB_PORT"), 1433))
    db_encrypt: bool = field(default_factory=lambda: _as_bool(os.getenv("DB_ENCRYPT"), False))
    db_trust_server_certificate: bool = field(
        default_factory=lambda: _as_bool(os.getenv("DB_TRUST_SERVER_CERTIFICATE"), True)
    )
    admin_user: str = field(default_factory=lambda: os.getenv("ADMIN_USER", "admin"))
    admin_password: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", "admin"))
    cors_origins: list[str] = field(
        default_factory=lambda: [
            o.strip()
            for o in os.getenv("CORS_ORIGIN", "http://localhost:5173,http://localhost:5174").split(",")
            if o.strip()
        ]
    )
    host: str = field(default_factory=lambda: os.getenv("FASTAPI_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: _as_int(os.getenv("FASTAPI_PORT"), 8000))


settings = Settings()
