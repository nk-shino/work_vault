"""スモークテスト: 全ページが 200 を返し、画面の骨格（テーマ・ナビ・表）がある。"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vbaglossary.db.guards import register_guards  # noqa: E402
from vbaglossary.db.session import make_engine, make_session_factory  # noqa: E402
from vbaglossary.vba.analyzer import analyze  # noqa: E402
from vbaglossary.web.app import create_app  # noqa: E402

register_guards()

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "vba"


@pytest.fixture(scope="module")
def client(tmp_path_factory: pytest.TempPathFactory) -> Iterator[TestClient]:
    tmp = tmp_path_factory.mktemp("smoke")
    url = f"sqlite:///{(tmp / 'smoke.db').as_posix()}"
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")
    session = make_session_factory(make_engine(url))()
    analyze(session, FIXTURES)
    session.close()
    app = create_app(url)
    with TestClient(app) as c:
        yield c


PAGES = [
    "/",
    "/procedures",
    "/procedures?q=Wait&learned=no",
    "/procedures?kind=Function",
    "/proposals",
    "/proposals?state=hold",
    "/review",
]


@pytest.mark.parametrize("path", PAGES)
def test_page_ok(client: TestClient, path: str) -> None:
    r = client.get(path)
    assert r.status_code == 200, path
    assert 'data-theme="auto"' in r.text
    assert "pillnav" in r.text


def test_static_served(client: TestClient) -> None:
    assert client.get("/static/style.css").status_code == 200
    js = client.get("/static/app.js")
    assert js.status_code == 200
    assert "prefers-reduced-motion" in client.get("/static/style.css").text


def test_list_shows_fixture_procedures(client: TestClient) -> None:
    r = client.get("/procedures")
    assert "WaitMain" in r.text
    assert "ImportData" in r.text


def test_tag_filter(client: TestClient) -> None:
    r = client.get("/procedures?tag=error-handling")
    assert "WaitMain" in r.text
    assert "ImportData" not in r.text


def test_hold_proposal_visible_and_masked(client: TestClient) -> None:
    r = client.get("/proposals?state=hold")
    assert "ConnectDb" in r.text
    assert "dummy-pass-1234" not in r.text
