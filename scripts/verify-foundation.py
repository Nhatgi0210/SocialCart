"""Run baseline tests on fresh isolated MySQL schemas; keep them for inspection.

Start docker-compose.verify.yml first. Credentials stay in ignored .cache/boot.env.
No DROP DATABASE, FLUSHDB or application DATABASE_URL is used.
"""
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from dotenv import dotenv_values
import pymysql
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info[:2] != (3, 11):
        raise SystemExit("Run with Python 3.11 (see .python-version)")
    password = os.environ.get("SC_VERIFY_MYSQL_PASSWORD") or dotenv_values(ROOT / ".cache/boot.env").get("SC_VERIFY_MYSQL_PASSWORD")
    if not password:
        raise SystemExit("Set SC_VERIFY_MYSQL_PASSWORD or create .cache/boot.env")
    connection = pymysql.connect(host="127.0.0.1", port=13306, user="root", password=password,
                                 autocommit=True, connect_timeout=5, read_timeout=10, write_timeout=10)
    suffix = uuid4().hex[:12]
    auth_db = f"socialcart_test_{suffix}"
    migration_db = f"socialcart_{suffix}_migration_test"
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        if not version.startswith("8.0."):
            raise SystemExit("Verification requires MySQL 8.0")
        for name in (auth_db, migration_db):
            cursor.execute(f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    connection.close()
    url = URL.create("mysql+aiomysql", username="root", password=password, host="127.0.0.1", port=13306, database=auth_db)
    env = dict(os.environ, PYTHONUTF8="1",
               SC_TEST_DATABASE_URL=url.render_as_string(hide_password=False),
               SC_TEST_REDIS_URL="redis://127.0.0.1:16379/15",
               SOCIALCART_MIGRATION_TEST_URL=url.set(database=migration_db).render_as_string(hide_password=False))
    print(f"Python {sys.version.split()[0]}; MySQL {version}; schemas {auth_db}, {migration_db}", flush=True)
    return subprocess.call([sys.executable, "-m", "pytest", "backend/tests", "-q", "-p", "no:cacheprovider", *sys.argv[1:]], cwd=ROOT, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
