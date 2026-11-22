import secrets

import pytest
from sqlalchemy.engine import URL, make_url

from config import database_url


@pytest.fixture(autouse=True)
def clean_database_environment(monkeypatch):
    for name in (
        "DATABASE_URL",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
    ):
        monkeypatch.delenv(name, raising=False)


def test_database_components_preserve_special_characters(monkeypatch):
    values = {
        "POSTGRES_HOST": "database.internal",
        "POSTGRES_PORT": "55432",
        "POSTGRES_USER": "learner@team",
        "POSTGRES_PASSWORD": "p@ss:/?#%word",
        "POSTGRES_DB": "lessons",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    url = database_url()
    assert url.host == "database.internal"
    assert url.port == 55432
    assert url.username == "learner@team"
    assert url.password == values["POSTGRES_PASSWORD"]
    assert url.database == "lessons"
    assert make_url(url.render_as_string(hide_password=False)) == url


def test_url_override_preserves_connection_options(monkeypatch):
    monkeypatch.setenv("POSTGRES_PORT", "unused-invalid-port")
    override = URL.create(
        "postgresql",
        username="override",
        password=secrets.token_urlsafe(24),
        host="remote",
        database="app",
        query={"sslmode": "require"},
    )
    monkeypatch.setenv("DATABASE_URL", override.render_as_string(hide_password=False))
    url = database_url()
    assert url.drivername == "postgresql+psycopg"
    assert url.host == "remote"
    assert url.password == override.password
    assert url.query["sslmode"] == "require"
    assert database_url("postgresql://explicit/db").host == "explicit"


def test_empty_url_uses_component_defaults(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "")
    url = database_url()
    assert url.drivername == "postgresql+psycopg"
    assert (url.username, url.password, url.database) == ("study_hall",) * 3
    assert (url.host, url.port) == ("localhost", 5432)


def test_rejects_non_postgres_url():
    with pytest.raises(ValueError, match="PostgreSQL"):
        database_url("sqlite:///:memory:")
