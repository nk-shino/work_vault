"""テスト共通の準備。DB は tmp_path にマイグレーションまで適用した実物を使う。"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from vbaglossary.db.guards import register_guards
from vbaglossary.db.models import Book, Module, Procedure, new_id
from vbaglossary.db.session import make_engine, make_session_factory

register_guards()

ROOT = Path(__file__).resolve().parents[1]


def _make_db(url: str) -> None:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    _make_db(url)
    return url


@pytest.fixture
def session_factory(db_url: str) -> Callable[[], Session]:
    return make_session_factory(make_engine(db_url))


@pytest.fixture
def db(session_factory: Callable[[], Session]) -> Iterator[Session]:
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def procedure(db: Session) -> Procedure:
    book = Book(
        id=new_id("b"),
        name="demo.xlsm",
        path="C:/work/demo.xlsm",
        sha256="sha-demo",
        analyzed_at=datetime.now(),
    )
    module = Module(
        id=new_id("m"),
        book_id=book.id,
        name="Module1",
        kind="standard",
        file_name="Module1.bas",
    )
    proc = Procedure(
        id=new_id("p"),
        module_id=module.id,
        name="WaitMain",
        kind="Function",
        access="Public",
        signature="Function WaitMain(title As String) As Boolean",
        returns="Boolean",
        start_line=1,
        end_line=5,
        line_count=5,
        source_key="sha-demo:Module1:WaitMain",
    )
    db.add_all([book, module, proc])
    db.commit()
    return proc
