import subprocess
import sys

from sqlalchemy import inspect

from tests.conftest import test_engine


def test_alembic_upgrade_head_applies_cleanly():
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


async def test_expected_tables_exist():
    async with test_engine.connect() as conn:
        table_names = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())

    assert {"runs", "tasks", "blackboard_entries"}.issubset(set(table_names))
