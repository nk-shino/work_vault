"""受入テスト: 解析→提案→受理→編集→評価→見送り→履歴 まで画面操作の流れを通す。"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vbaglossary.db.guards import register_guards  # noqa: E402
from vbaglossary.db.models import History, Proposal, Sense  # noqa: E402
from vbaglossary.db.session import make_engine, make_session_factory  # noqa: E402
from vbaglossary.vba.analyzer import analyze  # noqa: E402
from vbaglossary.web.app import create_app  # noqa: E402

register_guards()

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "vba"


@pytest.fixture(scope="module")
def env(tmp_path_factory: pytest.TempPathFactory) -> Iterator[dict]:
    tmp = tmp_path_factory.mktemp("accept")
    url = f"sqlite:///{(tmp / 'accept.db').as_posix()}"
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["database_url"] = url
    command.upgrade(cfg, "head")
    session = make_session_factory(make_engine(url))()
    result = analyze(session, FIXTURES)
    session.close()
    app = create_app(url)
    with TestClient(app) as client:
        yield {
            "client": client,
            "url": url,
            "session_factory": make_session_factory(make_engine(url)),
            "result": result,
        }


def _db(env: dict) -> Session:
    return env["session_factory"]()


def _find_proc_id(env: dict, name: str) -> str:
    db = _db(env)
    from vbaglossary.db.models import Procedure

    pid = db.scalar(select(Procedure.id).where(Procedure.name == name))
    db.close()
    assert pid is not None
    return str(pid)


def _find_proposal(env: dict, proc_id: str) -> tuple[str, str]:
    db = _db(env)
    proposal = db.scalar(
        select(Proposal).where(Proposal.procedure_id == proc_id, Proposal.decided_at.is_(None))
    )
    assert proposal is not None
    out = (str(proposal.id), str(proposal.draft_text))
    db.close()
    return out


def test_accept_flow_makes_sense(env: dict) -> None:
    client: TestClient = env["client"]
    pid = _find_proc_id(env, "WaitSeconds")
    proposal_id, draft = _find_proposal(env, pid)
    r = client.get(f"/procedures/{pid}")
    assert r.status_code == 200
    assert draft in r.text

    r = client.post(
        f"/proposals/{proposal_id}/accept",
        data={"text": "指定秒数だけ待って True を返す。", "reason": "確認して受理"},
        follow_redirects=False,
    )
    assert r.status_code == 303

    r = client.get(f"/procedures/{pid}")
    assert "指定秒数だけ待って True を返す。" in r.text
    assert "第 1 版" in r.text

    db = _db(env)
    proposal = db.get(Proposal, proposal_id)
    assert proposal is not None and proposal.decided_at is not None
    accepts = db.scalars(
        select(History).where(History.entity == "proposals", History.entity_id == proposal_id)
    ).all()
    assert accepts
    db.close()


def test_edit_conflict_then_success(env: dict) -> None:
    client: TestClient = env["client"]
    pid = _find_proc_id(env, "WaitSeconds")
    db = _db(env)
    sense = db.scalar(select(Sense).where(Sense.procedure_id == pid))
    assert sense is not None
    sense_id, version = str(sense.id), int(sense.version)
    db.close()

    r = client.post(
        f"/senses/{sense_id}/edit",
        data={"text": "新しい説明。", "reason": "言い直し", "expected_revision": version + 5},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "err=" in r.headers["location"]

    r = client.post(
        f"/senses/{sense_id}/edit",
        data={"text": "指定秒数だけ待機して成否を返す。", "reason": "表現を具体化", "expected_revision": version},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "msg=" in r.headers["location"]

    db = _db(env)
    sense = db.get(Sense, sense_id)
    assert sense is not None and sense.version == version + 1
    updates = [
        h
        for h in db.scalars(
            select(History).where(History.entity == "senses", History.entity_id == sense_id)
        ).all()
        if h.action == "update"
    ]
    assert updates
    db.close()

    r = client.get(f"/procedures/{pid}")
    assert "指定秒数だけ待機して成否を返す。" in r.text


def test_edit_requires_reason(env: dict) -> None:
    client: TestClient = env["client"]
    pid = _find_proc_id(env, "WaitSeconds")
    db = _db(env)
    sense = db.scalar(select(Sense).where(Sense.procedure_id == pid))
    assert sense is not None
    sense_id, version = str(sense.id), int(sense.version)
    db.close()
    r = client.post(
        f"/senses/{sense_id}/edit",
        data={"text": "理由なしの変更", "reason": " ", "expected_revision": version},
        follow_redirects=False,
    )
    assert "err=" in r.headers["location"]


def test_evaluate_and_review_page(env: dict) -> None:
    client: TestClient = env["client"]
    pid = _find_proc_id(env, "ImportData")
    proposal_id, _draft = _find_proposal(env, pid)
    client.post(
        f"/proposals/{proposal_id}/accept",
        data={"text": "設定シートの接続文字列でデータを取り込む。", "reason": "確認済み"},
        follow_redirects=False,
    )
    db = _db(env)
    sense = db.scalar(select(Sense).where(Sense.procedure_id == pid))
    assert sense is not None
    sense_id, version = str(sense.id), int(sense.version)
    db.close()

    r = client.post(
        f"/senses/{sense_id}/evaluate",
        data={"accuracy": "needs_fix", "usefulness": "useful", "seen_version": version, "reason": "文言が実態と違う"},
        follow_redirects=False,
    )
    assert r.status_code == 303

    r = client.get("/review")
    assert "修正が必要" in r.text


def test_evaluate_rejects_stale_version(env: dict) -> None:
    client: TestClient = env["client"]
    pid = _find_proc_id(env, "ImportData")
    db = _db(env)
    sense = db.scalar(select(Sense).where(Sense.procedure_id == pid))
    assert sense is not None
    sense_id = str(sense.id)
    db.close()
    r = client.post(
        f"/senses/{sense_id}/evaluate",
        data={"accuracy": "correct", "usefulness": "useful", "seen_version": 99},
        follow_redirects=False,
    )
    assert "err=" in r.headers["location"]


def test_hold_proposal_cannot_be_accepted(env: dict) -> None:
    client: TestClient = env["client"]
    db = _db(env)
    proposal = db.scalar(select(Proposal).where(Proposal.state == "hold"))
    assert proposal is not None
    pid = str(proposal.procedure_id)
    proposal_id = str(proposal.id)
    db.close()
    r = client.post(
        f"/proposals/{proposal_id}/accept",
        data={"text": "無理やり受理", "reason": "確認"},
        follow_redirects=False,
    )
    assert "err=" in r.headers["location"]
    r = client.get(f"/procedures/{pid}")
    assert "無理やり受理" not in r.text


def test_reject_flow(env: dict) -> None:
    client: TestClient = env["client"]
    pid = _find_proc_id(env, "LogWrite")
    proposal_id, _draft = _find_proposal(env, pid)
    r = client.post(
        f"/proposals/{proposal_id}/reject",
        data={"reason": "補助ルーチンなので語義にしない"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    r = client.get(f"/procedures/{pid}")
    assert "待ち受け中の提案はありません" in r.text


def test_code_page_and_history_pages(env: dict) -> None:
    client: TestClient = env["client"]
    pid = _find_proc_id(env, "WaitMain")
    r = client.get(f"/procedures/{pid}/code")
    assert r.status_code == 200
    assert "WaitMain" in r.text
    r = client.get(f"/history/procedures/{pid}")
    assert r.status_code == 200
    assert "create" in r.text or "解析" in r.text


def test_mixed_name_warning(env: dict) -> None:
    client: TestClient = env["client"]
    db = _db(env)

    from vbaglossary.db.models import Book, Module, Procedure, new_id

    book = db.scalar(select(Book).limit(1))
    assert book is not None
    module = Module(
        id=new_id("m"),
        book_id=book.id,
        name="ModuleOther",
        kind="standard",
        file_name="ModuleOther.bas",
    )
    twin = Procedure(
        id=new_id("p"),
        module_id=module.id,
        name="WaitSeconds",
        kind="Function",
        access="Private",
        signature="Private Function WaitSeconds(n As Long) As Boolean",
        returns="Boolean",
        start_line=1,
        end_line=2,
        line_count=2,
        source_key="acceptance-test:ModuleOther:WaitSeconds",
    )
    db.add_all([module, twin])
    db.commit()
    db.close()

    pid = _find_proc_id(env, "WaitSeconds")
    r = client.get(f"/procedures/{pid}")
    assert "混同注意" in r.text
