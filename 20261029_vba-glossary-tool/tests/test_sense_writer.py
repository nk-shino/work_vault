"""sense_writer の約束事: 用例必須・400字・書き込み経路・履歴・楽観ロック。"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from vbaglossary.db.guards import DeletionBlocked, WritePathError
from vbaglossary.db.models import Evidence, History, Procedure, Sense
from vbaglossary.domain import review
from vbaglossary.domain import sense_writer as sw
from vbaglossary.domain.errors import ConflictError, ValidationFailed
from vbaglossary.domain.sense_writer import EvidenceInput

EV = EvidenceInput(source_key="sha-demo:Module1:WaitMain:1", excerpt="Function WaitMain(title As String) As Boolean", masked=True)


def test_evidence_required(db: Session, procedure: Procedure) -> None:
    with pytest.raises(ValidationFailed, match="用例"):
        sw.create_sense(db, procedure, text="待機を制御する。", evidences=[])


def test_excerpt_over_400_rejected(db: Session, procedure: Procedure) -> None:
    long_ev = EvidenceInput(source_key="k", excerpt="a" * 401, masked=True)
    with pytest.raises(ValidationFailed, match="400"):
        sw.create_sense(db, procedure, text="説明", evidences=[long_ev])


def test_write_outside_scope_rejected(db: Session, procedure: Procedure) -> None:
    with pytest.raises(WritePathError):
        db.add(Sense(id="s_x", procedure_id=procedure.id, first_evidence_id="e_x", text="直接書き込み"))
        db.flush()


def test_delete_blocked(db: Session, procedure: Procedure) -> None:
    with pytest.raises(DeletionBlocked):
        db.delete(procedure)
        db.flush()


def test_create_and_read_back(db: Session, procedure: Procedure) -> None:
    sense = sw.create_sense(db, procedure, text="引数の題名を表示して待機し、成否を返す。", evidences=[EV])
    db.commit()
    fetched = db.scalar(select(Sense).where(Sense.id == sense.id))
    assert fetched is not None
    assert fetched.version == 1
    evidences = db.scalars(select(Evidence).where(Evidence.sense_id == sense.id)).all()
    assert len(evidences) == 1


def test_update_requires_reason(db: Session, procedure: Procedure) -> None:
    sense = sw.create_sense(db, procedure, text="旧説明。", evidences=[EV])
    db.commit()
    with pytest.raises(ValidationFailed, match="理由"):
        review.edit_sense(db, sense.id, expected_revision=1, text="新説明。", reason=" ")


def test_update_conflict(db: Session, procedure: Procedure) -> None:
    sense = sw.create_sense(db, procedure, text="旧説明。", evidences=[EV])
    db.commit()
    with pytest.raises(ConflictError):
        review.edit_sense(db, sense.id, expected_revision=99, text="新説明。", reason="差し替え")


def test_update_writes_history(db: Session, procedure: Procedure) -> None:
    sense = sw.create_sense(db, procedure, text="旧説明。", evidences=[EV])
    db.commit()
    review.edit_sense(db, sense.id, expected_revision=1, text="新説明。", reason="表現を具体化")
    db.commit()
    rows = db.scalars(select(History).where(History.entity == "senses", History.entity_id == sense.id)).all()
    actions = {r.action for r in rows}
    assert "update" in actions
    updated = db.get(Sense, sense.id)
    assert updated is not None and updated.version == 2
