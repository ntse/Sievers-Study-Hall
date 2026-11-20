"""Health probes independent of user sessions and page rendering."""

from flask import Blueprint, current_app
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from users.rate_limiting.config import RateLimitConfig
from users.users.models import db

health_bp = Blueprint("health", __name__)


@health_bp.after_request
def disable_caching(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@health_bp.get("/health/live")
def live():
    return {"status": "ok"}


@health_bp.get("/health/ready")
def ready():
    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        if RateLimitConfig.ENABLED and RateLimitConfig.BACKEND == "redis":
            with Redis.from_url(
                RateLimitConfig.REDIS_URL,
                socket_connect_timeout=1,
                socket_timeout=1,
            ) as client:
                client.ping()
    except (SQLAlchemyError, RedisError, OSError, ValueError):
        current_app.logger.warning("Readiness dependency check failed")
        return {"status": "unavailable"}, 503
    return {"status": "ready"}
