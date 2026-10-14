from __future__ import annotations

from pathlib import Path

from .env import database_config, get_bool, get_csv, get_env, load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
APP_ENV = get_env("APP_ENV", default="local")
if APP_ENV not in {"local", "test", "demo", "production"}:
    raise RuntimeError("APP_ENV must be local, test, demo or production.")

SECRET_KEY = get_env("DJANGO_SECRET_KEY", required=True)
DEBUG = get_bool("DJANGO_DEBUG", default=False)
if APP_ENV in {"demo", "production"} and DEBUG:
    raise RuntimeError("DJANGO_DEBUG cannot be enabled in demo or production.")

ALLOWED_HOSTS = get_csv("DJANGO_ALLOWED_HOSTS", default=("localhost", "127.0.0.1", "testserver"))
# A test process never follows an operator's DATABASE_URL by accident.
DATABASES = {"default": database_config(None if APP_ENV == "test" else get_env("DATABASE_URL"), str(BASE_DIR))}

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "identity",
    "catalog",
    "inventory",
    "cash",
    "sales",
    "app_platform",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_USER_MODEL = "identity.Account"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
# The application login is served from the public root, not Django's default
# /accounts/login/ route.  Keep anonymous protected-route redirects inside the
# published application.
LOGIN_URL = "/"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = APP_ENV in {"demo", "production"}
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = APP_ENV in {"demo", "production"}
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = APP_ENV in {"demo", "production"}
SECURE_HSTS_SECONDS = 31_536_000 if APP_ENV in {"demo", "production"} else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = APP_ENV in {"demo", "production"}
SECURE_HSTS_PRELOAD = APP_ENV in {"demo", "production"}
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if APP_ENV in {"demo", "production"} else None

SENSITIVE_POST_PARAMETERS = {"password", "password1", "password2", "csrfmiddlewaretoken"}
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"redact": {"()": "app_platform.logging.RedactSensitiveDataFilter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "filters": ["redact"]}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
