from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from flask import Flask
from flask_migrate import Migrate, downgrade, upgrade
from sqlalchemy import create_engine, inspect

from users.users.models import db


def test_migration_matches_models_and_can_be_reapplied(database_uri):
    engine = create_engine(database_uri)
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        assert context.get_current_revision() == "0002"
        assert compare_metadata(context, db.metadata) == []
    engine.dispose()

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    db.init_app(app)
    Migrate(app, db, directory=str(Path(__file__).resolve().parents[1] / "migrations"))
    with app.app_context():
        downgrade(revision="base")
        assert set(inspect(db.engine).get_table_names()) == {"alembic_version"}
        upgrade()
        upgrade()  # Repeated startup must be safe.
        with db.engine.connect() as conn:
            assert compare_metadata(MigrationContext.configure(conn), db.metadata) == []
        db.engine.dispose()
