"""`alembic/structure.sql` must match the declaration it was rendered from.

The point of a checked-in schema snapshot is that a change to the collection -- a different
distance metric, a new field, a toolkit upgrade that alters the chunk table -- lands in a diff a
reviewer can see. That only holds if the file cannot go stale, which is what this enforces.

No database and no `pg_dump`: this renders the declaration in-process.
"""

import pytest

from search_app import postgres_migration_url
from search_app.postgres_structure import STRUCTURE_PATH, render_structure


def test_structure_sql_is_current() -> None:
    assert STRUCTURE_PATH.exists(), f"{STRUCTURE_PATH} is missing; run `make structure`"
    assert STRUCTURE_PATH.read_text() == render_structure(), (
        f"{STRUCTURE_PATH.name} is stale -- the collection declaration has changed. Run "
        "`make structure` and commit the result, and add an Alembic revision for the same "
        "change if the table's shape moved."
    )


def test_structure_sql_covers_the_indexes_the_store_queries() -> None:
    """A snapshot nobody reads is worth little; pin the parts that carry the performance."""
    rendered = render_structure()
    assert "USING hnsw" in rendered
    assert "halfvec_cosine_ops" in rendered
    assert "_positional_idx" in rendered


def test_the_migration_url_normalises_any_driver_the_store_accepts(monkeypatch: pytest.MonkeyPatch) -> None:
    """The store overwrites whatever driver a DSN carries, so Alembic has to as well.

    `postgresql+asyncpg://` is a legitimate POSTGRES_DSN — `PostgresConnectionConfig.url` sets
    the driver rather than assuming it. A literal `postgresql://` replace would pass that
    through untouched and hand Alembic a URL it cannot drive synchronously.
    """
    for dsn in ("postgresql://u:p@h:5432/d", "postgresql+asyncpg://u:p@h:5432/d", "postgresql+psycopg://u:p@h:5432/d"):
        monkeypatch.setenv("POSTGRES_DSN", dsn)
        assert postgres_migration_url().startswith("postgresql+psycopg://"), dsn
        assert postgres_migration_url().endswith("@h:5432/d")
