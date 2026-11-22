"""Copy a stopped SQLite database into an empty PostgreSQL database."""

import argparse
from pathlib import Path

from sqlalchemy import MetaData, create_engine, func, select, text
from sqlalchemy.engine import URL

from config import database_url
from users.users.models import db


def migrate(source_path, target_url):
    source_path = Path(source_path).resolve(strict=True)
    source = create_engine(
        URL.create(
            "sqlite", database=source_path.as_uri(), query={"mode": "ro", "uri": "true"}
        )
    )
    target = create_engine(database_url(target_url))
    counts = {}
    try:
        source_metadata = MetaData()
        source_metadata.reflect(source)
        tables = db.metadata.sorted_tables
        for table in tables:
            if table.name not in source_metadata.tables:
                raise ValueError(f"Source is missing table {table.name}")
            missing = set(table.columns.keys()) - set(
                source_metadata.tables[table.name].columns.keys()
            )
            if missing:
                raise ValueError(
                    f"Source {table.name} is missing columns: {sorted(missing)}"
                )
        with source.connect() as old, target.begin() as new:
            db.metadata.create_all(new)
            # Block writes while checking and copying. The application must be stopped.
            names = ", ".join(
                new.dialect.identifier_preparer.quote(t.name) for t in tables
            )
            new.execute(text(f"LOCK TABLE {names} IN ACCESS EXCLUSIVE MODE"))
            for table in tables:
                if new.scalar(select(func.count()).select_from(table)):
                    raise ValueError(
                        f"Target table {table.name} is not empty; refusing to merge"
                    )
            for table in tables:
                source_table = source_metadata.tables[table.name]
                result = old.execute(
                    select(*(source_table.c[c.name] for c in table.columns))
                )
                counts[table.name] = 0
                for batch in result.mappings().partitions(1000):
                    new.execute(table.insert(), [dict(row) for row in batch])
                    counts[table.name] += len(batch)
                if "id" in table.c:
                    quoted = new.dialect.identifier_preparer.quote(table.name)
                    new.execute(
                        text(
                            f"SELECT setval(pg_get_serial_sequence(:table, 'id'), COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM {quoted}"
                        ),
                        {"table": quoted},
                    )
        return counts
    finally:
        source.dispose()
        target.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Path to the existing SQLite file")
    args = parser.parse_args()
    for table, count in migrate(args.source, None).items():
        print(f"{table}: {count} rows copied")
