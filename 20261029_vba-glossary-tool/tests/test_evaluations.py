"""評価は追記専用。版が違う評価は拒否し、DB トリガーも書き換えと削除を止める。"""

from __future__ import annotations

import pytest
from sqlalchemy import text as sql_text
from sqlalchemy.exc import IntegrityError as SAIntegrityError
from sqlalchemy.orm import Session

from vbaglossary.db.models import Evaluation, Procedure, Sense
from vbaglossary.domain import evaluations as ev
from vbaglossary.domain import proposals as pr
from vbaglossary.domain.errors import ValidationFailed


def _make_sense(db: Session, procedure: Procedure) -> Sense:
    proposal = pr.add_proposal(
        db,
        procedure,
        state="new",
        draft_text="待機を制御する。",
        excerpt="Function WaitMain(title As String) As Boolean",
    )
    assert proposal is not None
    return pr.accept(db, proposal.id)


def test_evaluate_ok(db: Session, procedure: Procedure) -> None:
    sense = _make_sense(db, procedure)
    result = ev.evaluate(db, sense.id, seen_version=1, accuracy="correct", usefulness="useful")
    db.commit()
    assert db.get(Evaluation, result.id) is not None


def test_version_mismatch_rejected(db: Session, procedure: Procedure) -> None:
    sense = _make_sense(db, procedure)
    with pytest.raises(ValidationFailed, match="版"):
        ev.evaluate(db, sense.id, seen_version=2, accuracy="correct", usefulness="useful")


def test_invalid_values_rejected(db: Session, procedure: Procedure) -> None:
    sense = _make_sense(db, procedure)
    with pytest.raises(ValidationFailed):
        ev.evaluate(db, sense.id, seen_version=1, accuracy="maybe", usefulness="useful")


def test_evaluations_are_append_only(db: Session, procedure: Procedure) -> None:
    sense = _make_sense(db, procedure)
    result = ev.evaluate(db, sense.id, seen_version=1, accuracy="needs_fix", usefulness="useful", reason="語義の言い回しが実態と違う")
    db.commit()
    with pytest.raises(SAIntegrityError):
        db.execute(sql_text("update evaluations set accuracy = 'correct'"))
        db.flush()
    with pytest.raises(SAIntegrityError):
        db.execute(sql_text(f"delete from evaluations where id = '{result.id}'"))
        db.flush()
