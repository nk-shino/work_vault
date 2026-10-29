"""提案の重複排除・受理・見送り。受理は sense_writer を通ることを確かめる。"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from vbaglossary.db.models import History, Procedure, Proposal, Sense
from vbaglossary.domain import proposals as pr
from vbaglossary.domain.errors import NotFound, ValidationFailed


def _add(
    db: Session,
    procedure: Procedure,
    *,
    state: str = "new",
    draft_text: str = "待機を制御する。",
    excerpt: str = "Function WaitMain(title As String) As Boolean",
    draft_source: str = "auto",
    reason: str | None = None,
) -> Proposal:
    proposal = pr.add_proposal(
        db,
        procedure,
        state=state,
        draft_text=draft_text,
        excerpt=excerpt,
        draft_source=draft_source,
        reason=reason,
    )
    db.commit()
    assert proposal is not None
    return proposal


def test_same_content_not_duplicated(db: Session, procedure: Procedure) -> None:
    first = _add(db, procedure)
    second = pr.add_proposal(db, procedure, state="new", draft_text="待機を制御する。", excerpt="Function WaitMain(title As String) As Boolean")
    db.commit()
    assert second is None
    count = len(db.scalars(select(Proposal)).all())
    assert count == 1
    assert first.id


def test_changed_content_replaces_open_proposal(db: Session, procedure: Procedure) -> None:
    first = _add(db, procedure)
    replaced = pr.add_proposal(db, procedure, state="new", draft_text="引数の題名を表示して待機する。", excerpt="Function WaitMain(title As String) As Boolean")
    db.commit()
    assert replaced is not None
    assert replaced.id == first.id
    assert replaced.draft_text.startswith("引数の題名")


def test_accept_creates_sense_and_history(db: Session, procedure: Procedure) -> None:
    proposal = _add(db, procedure)
    sense = pr.accept(db, proposal.id, reason="確認して受理")
    db.commit()
    fetched = db.get(Sense, sense.id)
    assert fetched is not None
    assert fetched.procedure_id == procedure.id
    decided = db.get(Proposal, proposal.id)
    assert decided is not None and decided.decided_at is not None
    actions = {h.action for h in db.scalars(select(History)).all()}
    assert "accept" in actions


def test_accept_twice_rejected(db: Session, procedure: Procedure) -> None:
    proposal = _add(db, procedure)
    pr.accept(db, proposal.id)
    db.commit()
    with pytest.raises(ValidationFailed, match="処理済み"):
        pr.accept(db, proposal.id)


def test_hold_cannot_be_accepted_directly(db: Session, procedure: Procedure) -> None:
    proposal = _add(db, procedure, state="hold", reason="禁止情報を検知したため保留")
    with pytest.raises(ValidationFailed, match="保留"):
        pr.accept(db, proposal.id)


def test_reject_requires_reason(db: Session, procedure: Procedure) -> None:
    proposal = _add(db, procedure)
    with pytest.raises(ValidationFailed, match="理由"):
        pr.reject(db, proposal.id, reason=" ")


def test_accept_missing_proposal(db: Session) -> None:
    with pytest.raises(NotFound):
        pr.accept(db, "pr_none")
