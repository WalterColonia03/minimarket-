"""Small, dependency-free environment configuration helpers."""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured


def load_dotenv(path: Path | None = None) -> None:
    """Load a local .env without overriding real process environment variables."""
    env_path = path or Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            os.environ.setdefault(key, value.strip().strip('"').strip("'"))


def get_env(name: str, *, required: bool = False, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    if required and not value:
        raise ImproperlyConfigured(f"{name} must be configured through the environment.")
    return value


def get_bool(name: str, *, default: bool = False) -> bool:
    value = get_env(name)
    if value is None:
        return default
    if value.lower() in {"1", "true", "yes", "on"}:
        return True
    if value.lower() in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean value.")


def get_csv(name: str, *, default: tuple[str, ...] = ()) -> list[str]:
    value = get_env(name)
    if value is None:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def database_config(url: str | None, base_dir: str) -> dict[str, object]:
    """Return Django's database dictionary from a PostgreSQL URL or local SQLite."""
    if not url:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": f"{base_dir}/r1_pmv.sqlite3",
        }

    parsed = urlparse(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured("DATABASE_URL must use postgresql://.")
    if not parsed.hostname or not parsed.path:
        raise ImproperlyConfigured("DATABASE_URL must include host and database name.")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parsed.path.lstrip("/")),
        "USER": unquote(parsed.username) if parsed.username else None,
        "PASSWORD": unquote(parsed.password) if parsed.password else None,
        "HOST": parsed.hostname,
        "PORT": parsed.port or 5432,
        "CONN_MAX_AGE": 60,
    }
