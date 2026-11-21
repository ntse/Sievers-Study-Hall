"""Probe success, dependency outages, and isolation from user routes."""

from unittest.mock import patch

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.exc import OperationalError

from users.rate_limiting.config import RateLimitConfig
from webapp.health import health_bp


@pytest.fixture
def client(app, monkeypatch):
    app.register_blueprint(health_bp)
    monkeypatch.setattr(RateLimitConfig, "BACKEND", "memory")
    return app.test_client()


def test_live_does_not_query_database(client):
    with patch(
        "sqlalchemy.engine.Engine.connect", side_effect=AssertionError("DB accessed")
    ):
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
    assert response.headers["Cache-Control"] == "no-store"
    assert "Set-Cookie" not in response.headers


def test_ready(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json == {"status": "ready"}
    assert response.headers["Cache-Control"] == "no-store"


def test_database_outage(client):
    error = OperationalError("SELECT 1", {}, Exception("private connection details"))
    with patch("sqlalchemy.engine.Engine.connect", side_effect=error):
        response = client.get("/health/ready")
        assert client.get("/health/live").status_code == 200
    assert response.status_code == 503
    assert response.json == {"status": "unavailable"}


@pytest.mark.parametrize("available", [True, False])
def test_redis_readiness(client, monkeypatch, available):
    monkeypatch.setattr(RateLimitConfig, "BACKEND", "redis")
    monkeypatch.setattr(RateLimitConfig, "ENABLED", True)
    with patch("webapp.health.Redis.from_url") as factory:
        redis_client = factory.return_value.__enter__.return_value
        if not available:
            redis_client.ping.side_effect = RedisConnectionError("private details")
        response = client.get("/health/ready")
        redis_client.ping.assert_called_once()
    assert response.status_code == (200 if available else 503)


def test_disabled_redis_is_not_required(client, monkeypatch):
    monkeypatch.setattr(RateLimitConfig, "BACKEND", "redis")
    monkeypatch.setattr(RateLimitConfig, "ENABLED", False)
    with patch("webapp.health.Redis.from_url") as factory:
        assert client.get("/health/ready").status_code == 200
        factory.assert_not_called()
