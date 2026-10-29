"""解析パイプラインの検査: 取り出し・切り分け・タグ・呼び出し・提案・マスキング・再解析。"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from vbaglossary.db.models import Module, Procedure, Proposal, Sense
from vbaglossary.domain import proposals as pr
from vbaglossary.settings import load_settings
from vbaglossary.vba.analyzer import analyze
from vbaglossary.vba.extract import extract_modules
from vbaglossary.vba.mask import mask, scan
from vbaglossary.vba.parse import parse_module

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "vba"


def _proc(db: Session, name: str) -> Procedure:
    proc = db.scalar(select(Procedure).where(Procedure.name == name))
    assert proc is not None
    return proc


def test_extract_and_parse() -> None:
    mods = {m.name: m for m in extract_modules(FIXTURES)}
    assert set(mods) == {"ModWait", "ModLegacy", "ModRisky"}
    assert "Attribute" not in mods["ModWait"].code
    procs = {p.name: p for p in parse_module(mods["ModWait"])}
    assert set(procs) == {"WaitMain", "WaitSeconds", "CommandButton1_Click"}
    wait = procs["WaitMain"]
    assert wait.kind == "Function"
    assert wait.access == "Public"
    assert wait.returns == "Boolean"
    assert [p.name for p in wait.params] == ["title", "seconds"]
    assert wait.params[1].optional is True
    assert wait.params[1].default == "3"
    assert "WaitSeconds" in wait.calls
    assert "error-handling" in wait.tags
    assert wait.comment_text.startswith("引数の題名")


def test_property_and_continuation(tmp_path: Path) -> None:
    (tmp_path / "ModProp.bas").write_text(
        "Option Explicit\n\n"
        "Private mCount As Long\n\n"
        "Public Property Get Count() As Long\n"
        "    Count = mCount\n"
        "End Property\n\n"
        "Public Property Let Count(ByVal v As Long)\n"
        "    mCount = v\n"
        "End Property\n\n"
        "Public Sub ShowMsg(msg As String, _\n"
        "                   title As String)\n"
        "    MsgBox msg, , title\n"
        "End Sub\n",
        encoding="utf-8",
    )
    mods = {m.name: m for m in extract_modules(tmp_path)}
    procs_list = parse_module(mods["ModProp"])
    procs = {p.name: p for p in procs_list}
    assert set(procs) == {"Count", "ShowMsg"}
    counts = [p for p in procs_list if p.name == "Count"]
    assert {p.kind for p in counts} == {"Property Get", "Property Let"}
    show = procs["ShowMsg"]
    assert [p.name for p in show.params] == ["msg", "title"]


def test_analyze_creates_modules_procedures_proposals(db: Session) -> None:
    result = analyze(db, FIXTURES)
    assert result.modules == 3
    assert result.procedures == 6
    assert result.proposals_added == 6
    wait = _proc(db, "WaitMain")
    assert wait is not None
    assert json.loads(wait.called_by_json)
    module = db.get(Module, wait.module_id)
    assert module is not None and module.name == "ModWait"
    click = _proc(db, "CommandButton1_Click")
    assert click is not None and "event" in json.loads(click.tags_json)
    legacy = _proc(db, "ImportData")
    assert {"loop", "select-case"} <= set(json.loads(legacy.tags_json))
    drafts = db.scalars(select(Proposal)).all()
    comment_drafts = [p for p in drafts if p.draft_source == "comment"]
    assert comment_drafts, "コメント付きプロシージャから draft が作られている"
    assert all(p.state in ("new", "hold") for p in drafts)


def test_analyze_masks_forbidden_info(db: Session) -> None:
    analyze(db, FIXTURES)
    risky = _proc(db, "ConnectDb")
    assert risky is not None
    proposal = db.scalar(select(Proposal).where(Proposal.procedure_id == risky.id))
    assert proposal is not None
    assert proposal.state == "hold"
    assert "dummy-pass-1234" not in proposal.excerpt
    assert "another-secret-99" not in proposal.excerpt
    assert "■" in proposal.excerpt


def test_reanalyze_is_idempotent(db: Session) -> None:
    analyze(db, FIXTURES)
    second = analyze(db, FIXTURES)
    assert second.new_procedures == 0
    assert second.updated_procedures == 0
    assert second.proposals_added == 0
    assert second.proposals_updated == 0


def test_reanalyze_updates_changed_definition(db: Session, tmp_path: Path) -> None:
    work = tmp_path / "book"
    work.mkdir()
    (work / "ModA.bas").write_text(
        "Public Sub Alpha()\n    Debug.Print 1\nEnd Sub\n", encoding="utf-8"
    )
    analyze(db, work)
    (work / "ModA.bas").write_text(
        "Public Sub Alpha(beta As Long)\n    Debug.Print beta\nEnd Sub\n", encoding="utf-8"
    )
    result = analyze(db, work)
    assert result.updated_procedures == 1
    alpha = _proc(db, "Alpha")
    assert alpha is not None and "beta" in alpha.signature


def test_accept_flow_after_analyze(db: Session) -> None:
    analyze(db, FIXTURES)
    wait = _proc(db, "WaitSeconds")
    assert wait is not None
    proposal = db.scalar(select(Proposal).where(Proposal.procedure_id == wait.id))
    assert proposal is not None
    sense = pr.accept(db, proposal.id, text="秒数だけ待って True を返す。")
    db.commit()
    assert db.get(Sense, sense.id) is not None


def test_mask_rules() -> None:
    rules = str(load_settings().config_dir / "masking_rules.yaml")
    assert scan('password = "x1234567"', rules) == ["password_assign"]
    masked = mask('url = "Server=x;pwd=abc123;"', rules)
    assert "abc123" not in masked
