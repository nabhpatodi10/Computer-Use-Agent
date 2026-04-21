from logging.config import fileConfig

import sqlite_vec
from sqlalchemy import engine_from_config, event, pool

from alembic import context

import database.models  # noqa: F401 — registers all models with Base.metadata
from database.connection import Base
from settings import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.sync_database_url)

target_metadata = Base.metadata


def _load_vec_extension(dbapi_conn, _record) -> None:
    """Load sqlite-vec on the migration connection so `CREATE VIRTUAL TABLE
    ... USING vec0(...)` and other vec_* calls issued from migrations work."""
    dbapi_conn.enable_load_extension(True)
    sqlite_vec.load(dbapi_conn)
    dbapi_conn.enable_load_extension(False)


def _include_object(obj, name, type_, reflected, compare_to) -> bool:
    """Exclude the sqlite-vec virtual table and its shadow tables from
    autogenerate diffs. The main `user_memories` table has a SQLAlchemy
    model, so it's NOT excluded — autogenerate manages it normally."""
    if type_ == "table" and (
        name == "user_memories_vec" or name.startswith("user_memories_vec_")
    ):
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        include_object=_include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    event.listen(connectable, "connect", _load_vec_extension)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            include_object=_include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
