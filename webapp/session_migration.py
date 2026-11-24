"""Migrate data from legacy client-side session cookies to server-side sessions.

Remove once legacy cookies have expired (PERMANENT_SESSION_LIFETIME after deploy).
"""

from flask import request, session
from flask.sessions import SecureCookieSessionInterface
from itsdangerous import BadData


def _load_legacy_session(app, value):
    serializer = SecureCookieSessionInterface().get_signing_serializer(app)
    if serializer is None:
        return None
    try:
        data = serializer.loads(
            value, max_age=int(app.permanent_session_lifetime.total_seconds())
        )
    except BadData:
        return None
    return data if isinstance(data, dict) else None


def init_legacy_session_migration(app):
    cookie_name = app.config["LEGACY_SESSION_COOKIE_NAME"]

    @app.before_request
    def migrate_legacy_session():
        value = request.cookies.get(cookie_name)
        if not value or cookie_name == app.config["SESSION_COOKIE_NAME"]:
            return
        if not session:
            data = _load_legacy_session(app, value)
            if data:
                session.update(data)
                session.permanent = True
                session.modified = True

    @app.after_request
    def drop_legacy_cookie(response):
        if (
            cookie_name != app.config["SESSION_COOKIE_NAME"]
            and cookie_name in request.cookies
        ):
            response.delete_cookie(
                cookie_name,
                secure=app.config["SESSION_COOKIE_SECURE"],
                httponly=app.config["SESSION_COOKIE_HTTPONLY"],
                samesite=app.config["SESSION_COOKIE_SAMESITE"],
            )
        return response
