"""
config.py

Central configuration for the Finance Tracker app.
Reads secrets from .env and exposes them as clean Python values.
"""

import os
from dotenv import load_dotenv

# Load .env once, at import time, so every module gets the values.
load_dotenv()


class Config:
    """Application configuration values."""

    # PostgreSQL connection string (from Neon).
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # Secret key used by Flask to sign session cookies.
    # From .env locally; from Render env vars in production.
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Session cookie hardening.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Set to True only in production (over HTTPS).
    SESSION_COOKIE_SECURE = False


# Fail fast at import time if secrets are missing.
if not Config.DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Did you create .env from .env.example?"
    )
if not Config.SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. Did you create .env from .env.example?"
    )