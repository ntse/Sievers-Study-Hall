"""Tests for session security configuration."""

from datetime import timedelta


def test_session_lifetime_24_hours(app):
    """Session lifetime should be 24 hours."""
    assert app.config["PERMANENT_SESSION_LIFETIME"] == timedelta(hours=24)


def test_session_cookie_secure_flag(app):
    """Session cookies should require HTTPS."""
    assert app.config["SESSION_COOKIE_SECURE"] is True


def test_session_cookie_httponly_flag(app):
    """Session cookies should not be accessible to JavaScript."""
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True


def test_session_cookie_samesite(app):
    """Session cookies should use SameSite=Lax."""
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_preferred_url_scheme_https(app):
    """URLs should default to HTTPS scheme."""
    assert app.config["PREFERRED_URL_SCHEME"] == "https"


def test_session_permanent_enabled(app):
    """Session persistence should be enabled."""
    assert app.config["SESSION_PERMANENT"] is True
