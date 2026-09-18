"""Alembic environment for this project.

Two things are wired here, and neither is search-specific machinery.

``target_metadata`` is the table the collection declaration in ``search_app`` builds. That is
the whole of what putting a search collection into an Alembic chain takes: the collection's
table sits in the same metadata as any table of your own, under one ``alembic_version``. How
you write revisions against it is your choice -- this is an ordinary Alembic setup.

``load_dotenv(override=True)`` matches the entrypoints. Reading ``POSTGRES_DSN`` through the
same function is not enough on its own: if the entrypoints loaded ``.env`` and this did not,
migrations and the app could quietly be pointed at different databases. Because that override
means ``.env`` beats the process environment, a caller that needs a different database says so
through the Alembic config rather than an env var.
"""

from dotenv import load_dotenv

load_dotenv(override=True)  # before importing search_app, which reads the environment

from sqlalchemy import MetaData, engine_from_config, pool  # noqa: E402

from alembic import context  # noqa: E402
from search_app import POSTGRES_COLLECTION, postgres_migration_url  # noqa: E402

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
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


def run_migrations_offline() -> None:
    context.configure(
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
