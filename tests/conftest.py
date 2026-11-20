"""Shared test fixtures and utilities."""

import pytest
from flask import Blueprint, Flask
from flask_login import LoginManager

from users.rate_limiting.decorator import rate_limit_exercise_submission
from users.users.models import User, db


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
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

    @bp.route('/')
    def index():
        return "OK"

    app.register_blueprint(bp)

    # Add security headers middleware for testing
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    with app.app_context():
        db.create_all()
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
