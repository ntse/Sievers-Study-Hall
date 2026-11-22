"""Shared Flask session and URL configuration."""

import os
from datetime import timedelta
from typing import ClassVar

from sqlalchemy.engine import URL, make_url


def database_url(value=None):
    value = value or os.environ.get("DATABASE_URL")
    if value:
        url = make_url(value)
    else:
        url = URL.create(
            "postgresql+psycopg",
            username=os.environ.get("POSTGRES_USER", "study_hall"),
            password=os.environ.get("POSTGRES_PASSWORD", "study_hall"),
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            database=os.environ.get("POSTGRES_DB", "study_hall"),
        )
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")
    if url.drivername != "postgresql+psycopg":
        raise ValueError("DATABASE_URL must use PostgreSQL with psycopg")
    return url


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS: ClassVar[dict] = {"pool_pre_ping": True}
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PREFERRED_URL_SCHEME = "https"
