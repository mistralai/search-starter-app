"""`alembic/structure.sql` must match the declaration it was rendered from.

The point of a checked-in schema snapshot is that a change to the collection -- a different
distance metric, a new field, a toolkit upgrade that alters the chunk table -- lands in a diff a
reviewer can see. That only holds if the file cannot go stale, which is what this enforces.

No database and no `pg_dump`: this renders the declaration in-process.
"""

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
