"""Alembic environment for this project.

Two things are wired here, and neither is search-specific machinery.

``target_metadata`` is the table the collection declaration in ``search_app`` builds. That
is the whole of what putting a search collection into an Alembic chain takes: point
autogenerate at it and it writes static DDL for the collection alongside any tables of your
own, in one revision, under one ``alembic_version``. It is also what makes ``alembic check``
a drift test between the chain and what the running app expects.

The ``alembic_ops`` import adds ``op.build_vector_index`` to the ``op`` namespace -- the one
operation autogenerate cannot express, because building an HNSW index without blocking writes
is a choice about *how* a change rolls out rather than about the end state.

``load_dotenv(override=True)`` matches the entrypoints. Reading ``POSTGRES_DSN`` through the
same function is not enough on its own: if the entrypoints loaded ``.env`` and this did not,
migrations and the app could quietly be pointed at different databases. Because that override
means ``.env`` beats the process environment, a caller that needs a different database says so
through the Alembic config rather than an env var -- which is what ``tests/test_migrations.py``
does to run the chain against a database of its own.
"""

from dotenv import load_dotenv

load_dotenv(override=True)  # before importing search_app, which reads the environment

from sqlalchemy import MetaData, engine_from_config, pool  # noqa: E402

from alembic import context  # noqa: E402
from mistralai.search.toolkit.plugins.postgres import alembic_ops  # noqa: E402, F401 - registers the op
from search_app import POSTGRES_COLLECTION, include_object, postgres_migration_url  # noqa: E402

config = context.config
if not config.get_main_option("sqlalchemy.url", None):
    config.set_main_option("sqlalchemy.url", postgres_migration_url())

target_metadata = MetaData()
POSTGRES_COLLECTION.to_table(metadata=target_metadata)


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            # `compare_type` is Alembic's default (1.12+), pinned so a change of default cannot
            # silently stop catching an embedding-dimension change -- the dimension lives only in
            # the column type, and no index name encodes it. `compare_server_default` is not a
            # default, and the metadata column carries one.
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


def run_migrations_offline() -> None:
    context.configure(
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
