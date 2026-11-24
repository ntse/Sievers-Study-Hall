"""Tests for server-side sessions and legacy cookie migration."""

import pytest
from flask import Flask, jsonify, session
from flask.sessions import SecureCookieSessionInterface
from flask_session import Session
from sqlalchemy import text

from config import Config
from users.users.models import db
from webapp.session_migration import init_legacy_session_migration


@pytest.fixture
def session_app(database_uri):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.secret_key = "test-secret"
    db.init_app(app)
    app.config["SESSION_SQLALCHEMY"] = db
    Session(app)
    init_legacy_session_migration(app)

    @app.route("/get")
    def get():
        return jsonify(dict(session))

    @app.route("/set")
    def set_():
        session["progress"] = 3
        return "ok"

    return app


def legacy_cookie(app, data):
    serializer = SecureCookieSessionInterface().get_signing_serializer(app)
    return serializer.dumps(data)


def set_legacy(client, value):
    client.set_cookie("session", value, domain="localhost")


def test_legacy_cookie_data_migrated_and_cookie_removed(session_app):
    client = session_app.test_client()
    set_legacy(client, legacy_cookie(session_app, {"genus": {"1": 2}}))
    response = client.get("/get")
    assert response.json == {"genus": {"1": 2}, "_permanent": True}
    assert any(
        h.startswith("session=;") for h in response.headers.getlist("Set-Cookie")
    )
    assert client.get("/get").json["genus"] == {"1": 2}


def test_tampered_legacy_cookie_ignored(session_app):
    client = session_app.test_client()
    set_legacy(client, legacy_cookie(session_app, {"a": 1}) + "x")
    assert "a" not in client.get("/get").json


def test_session_stored_server_side(session_app):
    client = session_app.test_client()
    client.get("/set")
    assert client.get("/get").json["progress"] == 3
    with session_app.app_context():
        assert db.session.execute(text("select count(*) from sessions")).scalar() == 1
    cookie = client.get_cookie("sid")
    assert cookie is not None and "progress" not in cookie.value
