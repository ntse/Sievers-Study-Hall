"""Shared test fixtures and utilities."""

import os
import uuid
from pathlib import Path

import pytest
from flask import Blueprint, Flask
from flask_login import LoginManager
from flask_migrate import Migrate, upgrade
from sqlalchemy import create_engine, text

from config import Config, database_url
from users.rate_limiting.decorator import rate_limit_exercise_submission
from users.users.models import User, db


@pytest.fixture
def database_uri():
    """Isolate each test in its own Postgres schema, never drop shared tables."""
    url = database_url(
        os.environ.get(
            "TEST_DATABASE_URL",
            "postgresql+psycopg://study_hall:study_hall@localhost:5432/study_hall_test",
        )
    )
    engine = create_engine(url)
    schema = "test_" + uuid.uuid4().hex
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    try:
        scoped_url = url.update_query_dict({"options": f"-csearch_path={schema}"})
        migration_app = Flask(__name__)
        migration_app.config["SQLALCHEMY_DATABASE_URI"] = scoped_url
        db.init_app(migration_app)
        Migrate(
            migration_app,
            db,
            directory=str(Path(__file__).resolve().parents[1] / "migrations"),
        )
        with migration_app.app_context():
            upgrade()
            db.engine.dispose()
        yield scoped_url
    finally:
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()


@pytest.fixture
def app(database_uri):
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = "test-secret"

    db.init_app(app)

    login_manager = LoginManager(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create test blueprint with rate-limited endpoint
    bp = Blueprint("test", __name__)

    @bp.route("/test-endpoint", methods=["POST"])
    @rate_limit_exercise_submission
    def test_endpoint():
        return {"status": "ok"}

    @bp.route("/")
    def index():
        return "OK"

    app.register_blueprint(bp)

    # Add security headers middleware for testing
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        return response

    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


def make_test_user(email):
    """Create a test user."""
    user = User(email=email)
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def redis_client():
    """Get a fake Redis client for testing."""
    import fakeredis

    return fakeredis.FakeRedis(decode_responses=False)
