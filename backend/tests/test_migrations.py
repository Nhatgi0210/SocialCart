"""Opt-in integration test; only accepts a new, empty *_migration_test database."""
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


def test_mysql_upgrade_backfill_downgrade():
    raw_url = os.environ.get("SOCIALCART_MIGRATION_TEST_URL")
    if not raw_url:
        pytest.skip("Requires an empty dedicated MySQL migration test database")
    url = make_url(raw_url)
    assert url.database.endswith("_migration_test")
    engine = create_engine(url.set(drivername="mysql+pymysql"))
    assert inspect(engine).get_table_names() == [], "Refusing a non-empty database"
    config = Config(str(Path(__file__).parents[1] / "shared/db/alembic.ini"))
    # Use a supplied connection so the production DATABASE_URL is never used.
    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "0001_initial_schema")
        connection.execute(text("INSERT INTO users (id,email,hashed_password,is_active,created_at,updated_at) "
                                "VALUES ('00000000-0000-0000-0000-000000000001',"
                                "'migration@example.test','test-only-not-a-password',1,UTC_TIMESTAMP(),UTC_TIMESTAMP())"))
        connection.commit()
        command.upgrade(config, "head")
        assert connection.execute(text("SELECT name FROM users")).scalar_one() == "Chủ shop"
        assert len(inspect(connection).get_table_names()) == 18
        columns = inspect(connection).get_columns("users")
        assert not next(c for c in columns if c["name"] == "name")["nullable"]
        assert next(c for c in columns if c["name"] == "created_at")["type"].fsp == 6
        connection.commit()
        command.downgrade(config, "base")
        assert inspect(connection).get_table_names() == ["alembic_version"]
        command.upgrade(config, "head")
        assert len(inspect(connection).get_table_names()) == 18
        connection.commit()
    engine.dispose()
