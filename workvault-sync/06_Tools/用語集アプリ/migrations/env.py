"""Alembic の実行環境。接続先はテストから差し替えられるよう、引数を優先する。"""

from __future__ import annotations

from alembic import context

from glossary.db.session import make_engine
from glossary.settings import load_settings

config = context.config
url = config.attributes.get("database_url") or load_settings().database_url

engine = make_engine(url)
with engine.connect() as connection:
    context.configure(connection=connection, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()
engine.dispose()
