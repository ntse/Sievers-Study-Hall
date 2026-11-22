from unittest.mock import patch

import pytest
from flask import session
from flask_login import login_user
from sqlalchemy import JSON, MetaData, create_engine, select

from scripts.migrate_sqlite import migrate
from users.progress.progress import update_progress_in_home_page
from users.users.models import User, UserSettings, UserUnitHomeProgress, db


def test_json_mutation_and_progress_upsert(app):
    user = User(email="postgres@example.test")
    user.set_password("password")
    db.session.add(user)
    db.session.flush()
    settings = UserSettings(user_id=user.id, settings={"language": "fr"})
    db.session.add(settings)
    db.session.commit()
    settings.settings["language"] = "en"
    db.session.commit()
    db.session.expire_all()
    assert settings.settings == {"language": "en"}
    with app.test_request_context():
        login_user(user)
        with patch(
            "users.progress.progress.compute_completed_exercises", side_effect=[1, 2]
        ):
            update_progress_in_home_page(session, "genus")
            update_progress_in_home_page(session, "genus")
    assert UserUnitHomeProgress.query.one().completed_exercises == 2


def test_sqlite_import_preserves_data_and_sequences(database_uri, tmp_path):
    path = tmp_path / "old.db"
    source = create_engine(f"sqlite:///{path}")
    metadata = MetaData()
    for table in db.metadata.sorted_tables:
        copy = table.to_metadata(metadata)
        for column in copy.columns:
            if isinstance(column.type, JSON):
                column.type = JSON()
    metadata.create_all(source)
    with source.begin() as conn:
        conn.execute(
            metadata.tables["user"].insert(),
            {"id": 42, "email": "old@example.test", "password_hash": "existing-hash"},
        )
        conn.execute(
            metadata.tables["user_settings"].insert(),
            {"user_id": 42, "settings": {"language": "fr", "nested": ["é", 2]}},
        )
    source.dispose()
    assert migrate(path, database_uri)["user"] == 1
    target = create_engine(database_uri)
    with target.begin() as conn:
        assert conn.scalar(select(UserSettings.settings)) == {
            "language": "fr",
            "nested": ["é", 2],
        }
        assert conn.scalar(select(User.password_hash)) == "existing-hash"
        assert (
            conn.scalar(
                User.__table__.insert()
                .values(email="new@example.test", password_hash="hash")
                .returning(User.id)
            )
            == 43
        )
    with pytest.raises(ValueError, match="not empty"):
        migrate(path, database_uri)
    target.dispose()
