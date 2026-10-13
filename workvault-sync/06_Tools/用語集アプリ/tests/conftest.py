"""テスト全体の前提。外への通信を塞ぎ、LLM はモックに固定する。"""

from __future__ import annotations

import os
import socket
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

# import より前に固定する。settings が読まれた時点で値が決まるため
os.environ["GLOSSARY_TESTING"] = "1"
os.environ["LLM_BACKEND"] = "mock"
os.environ["SOURCE_BACKEND"] = "export"

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from glossary.db.session import make_engine, make_session_factory  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# ---- 外部通信の遮断 ----
# Windows の asyncio は内部で自分自身（127.0.0.1）へ接続して待ち合わせに使うので、
# ループバックだけは通す。それ以外の宛先への接続と名前解決は、試みた時点で失敗させて記録する。
BLOCKED: list[str] = []
_LOOPBACK = {"127.0.0.1", "::1", "localhost"}
_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex
_real_getaddrinfo = socket.getaddrinfo


class NetworkBlocked(RuntimeError):
    pass


def _host(address: Any) -> str:
    return str(address[0]) if isinstance(address, tuple) else str(address)


def _guard(address: Any) -> None:
    host = _host(address)
    if host not in _LOOPBACK:
        BLOCKED.append(host)
        raise NetworkBlocked(f"テスト中の外部通信を遮断: {host}")


def _connect(self: socket.socket, address: Any) -> None:
    _guard(address)
    _real_connect(self, address)


def _connect_ex(self: socket.socket, address: Any) -> int:
    _guard(address)
    return _real_connect_ex(self, address)


def _getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
    if host is not None and str(host) not in _LOOPBACK:
        BLOCKED.append(str(host))
        raise NetworkBlocked(f"テスト中の名前解決を遮断: {host}")
    return _real_getaddrinfo(host, *args, **kwargs)


socket.socket.connect = _connect  # type: ignore[method-assign]
socket.socket.connect_ex = _connect_ex  # type: ignore[method-assign]
socket.getaddrinfo = _getaddrinfo


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    # 遮断のテスト自身が意図的に1回試みるので、それ以外に試みがあれば失敗にする
    unexpected = [h for h in BLOCKED if h != "203.0.113.1"]
    if unexpected:
        print(f"\n外部通信の試みがあった: {unexpected}")
        session.exitstatus = 1


# ---- DB ----


def migrate(url: str) -> None:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")


@pytest.fixture
def db_url(tmp_path: Path) -> str:
    url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    migrate(url)
    return url


@pytest.fixture
def factory(db_url: str) -> sessionmaker[Session]:
    return make_session_factory(make_engine(db_url))


@pytest.fixture
def db(factory: sessionmaker[Session]) -> Iterator[Session]:
    with factory() as session:
        yield session
