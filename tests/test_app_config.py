"""Tests for app configuration and security settings."""

import importlib
import os
from unittest.mock import patch

import pytest

from config import Config
from users.users.models import db


def reload_app(app_module):
    """Reload app, dropping the session table Flask-Session registered on first import."""
    stale = db.metadata.tables.get(Config.SESSION_SQLALCHEMY_TABLE)
    if stale is not None:
        db.metadata.remove(stale)
    importlib.reload(app_module)


@pytest.fixture(autouse=True)
def restore_environment():
    with patch.dict(os.environ):
        # Importing app connects to the database, so point it at the test one.
        os.environ["DATABASE_URL"] = os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql+psycopg://study_hall:study_hall@localhost:5432/study_hall_test",
        )
        yield


def test_secret_key_production_required():
    """Secret key must be explicitly set in production."""
    os.environ["FLASK_ENV"] = "production"
    # Remove the env var to trigger the error
    if "FLASK_SECRET_KEY" in os.environ:
        del os.environ["FLASK_SECRET_KEY"]

    with pytest.raises(ValueError, match="FLASK_SECRET_KEY.*must be set"):
        import app as app_module

        reload_app(app_module)


def test_secret_key_development_fallback():
    """Secret key can fall back to dev value in development."""
    os.environ["FLASK_ENV"] = "development"
    if "FLASK_SECRET_KEY" in os.environ:
        del os.environ["FLASK_SECRET_KEY"]

    import app as app_module

    reload_app(app_module)
    assert app_module.app.secret_key == "dev-only-insecure-key"


def test_secret_key_from_env():
    """Secret key should be read from environment variable."""
    os.environ["FLASK_SECRET_KEY"] = "test-secret-key-12345"
    if "FLASK_ENV" in os.environ:
        del os.environ["FLASK_ENV"]

    import app as app_module

    reload_app(app_module)
    assert app_module.app.secret_key == "test-secret-key-12345"


def test_no_hardcoded_known_secret():
    """App should not use the old hardcoded secret key."""
    os.environ["FLASK_SECRET_KEY"] = "custom-secret"
    if "FLASK_ENV" in os.environ:
        del os.environ["FLASK_ENV"]

    import app as app_module

    reload_app(app_module)
    assert app_module.app.secret_key != "secret_key_for_development_environment"
