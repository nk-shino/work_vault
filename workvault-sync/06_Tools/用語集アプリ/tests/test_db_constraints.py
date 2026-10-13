"""データの約束事を、アプリ層と DB 層の両方で確かめる。

DB 層のテストは ORM とガードを経由せず SQL を直接流す。
「アプリのバグや別経路の書き込みがあっても DB が止める」ことを見たいので。
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest
from helpers import accepted_sense, evidence
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from glossary.db.guards import (
    MissingChangeReason,
    PhysicalDeleteForbidden,
    SenseWriteForbidden,
    edit_context,
)
from glossary.db.models import EXCERPT_MAX_LEN, Relation, Revision, Sense, Term
from glossary.domain import proposals, review
from glossary.domain.errors import ConflictError, ValidationFailed

NOW = "2031-04-01 00:00:00"


def raw(db: Session, sql: str, **params: object) -> None:
    db.execute(text(sql), params)


def insert_term(db: Session, tid: str = "t1") -> None:
    raw(
        db,
        "INSERT INTO terms (id, headword, status, revision_number, created_at, updated_at) "
        "VALUES (:id, '架空語', 'draft', 1, :now, :now)",
        id=tid,
        now=NOW,
    )


def insert_sense(db: Session, sid: str, first_evidence_id: str, tid: str = "t1") -> None:
    raw(
        db,
        "INSERT INTO senses (id, term_id, first_evidence_id, definition, source_type, status, "
        "revision_number, created_at, updated_at) "
        "VALUES (:id, :tid, :ev, '定義', 'human', 'confirmed', 1, :now, :now)",
        id=sid,
        tid=tid,
        ev=first_evidence_id,
        now=NOW,
    )


def insert_evidence(db: Session, eid: str, sid: str, excerpt: str = "用例") -> None:
    raw(
        db,
        "INSERT INTO evidences (id, sense_id, source_type, source_ref, excerpt, masked) "
        "VALUES (:id, :sid, 'mail', 'eml:1', :ex, 1)",
        id=eid,
        sid=sid,
        ex=excerpt,
    )


# ---- 用例の無い定義は保存できない ----


def test_app_rejects_sense_without_evidence(db: Session) -> None:
    p = proposals.add_proposal(
        db,
        proposal_type="sense",
        payload={"headword": "架空語", "definition": "定義", "evidences": []},
        model_name="mock-llm",
        prompt_version="t",
        score=None,
    )
    db.flush()
    with pytest.raises(ValidationFailed, match="用例"):
        proposals.accept(db, p.id, reviewer=None)


def test_db_rejects_sense_without_evidence(db: Session) -> None:
    insert_term(db)
    insert_sense(db, "s1", first_evidence_id="nonexistent")
    # 遅延外部キーなので、確かめられるのはコミット時
    with pytest.raises(IntegrityError):
        db.commit()


def test_db_rejects_sense_pointing_to_other_senses_evidence(db: Session) -> None:
    insert_term(db)
    insert_sense(db, "s1", first_evidence_id="e1")
    insert_evidence(db, "e1", "s1")
    db.commit()
    # s2 は s1 の用例を自分の用例だと言い張る
    insert_sense(db, "s2", first_evidence_id="e1")
    with pytest.raises(IntegrityError):
        db.commit()


def test_db_accepts_sense_with_its_own_evidence(db: Session) -> None:
    insert_term(db)
    insert_sense(db, "s1", first_evidence_id="e1")
    insert_evidence(db, "e1", "s1")
    db.commit()
    assert db.scalar(select(func.count()).select_from(Sense)) == 1


# ---- 語義へ書き込める経路は2つだけ ----


def test_direct_sense_insert_is_forbidden(db: Session) -> None:
    term = Term(headword="架空語", status="draft")
    with edit_context(db, "テスト", "直接書き込みの確認"):
        db.add(term)
        db.add(Sense(term=term, first_evidence_id="x", definition="定義", source_type="human"))
        with pytest.raises(SenseWriteForbidden):
            db.flush()


def test_direct_sense_update_is_forbidden(db: Session) -> None:
    sense = accepted_sense(db, "架空語")
    with edit_context(db, "テスト", "直接更新の確認"):
        sense.definition = "書き換え"
        with pytest.raises(SenseWriteForbidden):
            db.flush()


def test_change_without_reason_is_rejected(db: Session) -> None:
    db.add(Term(headword="架空語", status="draft"))
    with pytest.raises(MissingChangeReason):
        db.flush()


# ---- 関係 ----


def test_self_relation_rejected_by_app(db: Session) -> None:
    accepted_sense(db, "架空語")
    p = proposals.add_proposal(
        db,
        proposal_type="relation",
        payload={"from_headword": "架空語", "to_headword": "架空語",
                 "relation_type": "related", "method": "human"},
        model_name="human",
        prompt_version="t",
        score=None,
    )  # fmt: skip
    db.flush()
    with pytest.raises(ValidationFailed, match="同じ語義"):
        proposals.accept(db, p.id, reviewer=None)


def test_self_relation_rejected_by_db(db: Session) -> None:
    s = accepted_sense(db, "架空語")
    db.add(Relation(from_sense_id=s.id, to_sense_id=s.id, relation_type="related", method="human"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_relation_to_missing_sense_rejected(db: Session) -> None:
    s = accepted_sense(db, "架空語")
    db.add(Relation(from_sense_id=s.id, to_sense_id="nope", relation_type="related", method="human"))
    with pytest.raises(IntegrityError):
        db.flush()


# ---- 楽観ロックと履歴 ----


def test_stale_revision_is_not_overwritten(db: Session) -> None:
    sense = accepted_sense(db, "架空語", "元の定義")
    review.edit_sense(
        db, sense.id, expected_revision=1, changes={"definition": "Aさんの修正"},
        editor_name="A", change_reason="修正",
    )  # fmt: skip
    db.commit()
    # B は版1を見たまま保存しようとする
    with pytest.raises(ConflictError) as info:
        review.edit_sense(
            db, sense.id, expected_revision=1, changes={"definition": "Bさんの修正"},
            editor_name="B", change_reason="修正",
        )  # fmt: skip
    db.rollback()
    assert info.value.current["definition"] == "Aさんの修正"
    assert info.value.submitted["definition"] == "Bさんの修正"
    assert db.get(Sense, sense.id).definition == "Aさんの修正"  # type: ignore[union-attr]


def test_concurrent_update_detected_by_db(factory: sessionmaker[Session]) -> None:
    """版の確認を通り抜けた後に割り込まれても、UPDATE の WHERE revision_number で止まる。"""
    with factory() as setup:
        sid = accepted_sense(setup, "架空語").id
    with factory() as a, factory() as b:
        sa, sb = a.get(Sense, sid), b.get(Sense, sid)
        assert sa is not None and sb is not None
        review.edit_sense(
            a, sid, expected_revision=1, changes={"definition": "A"},
            editor_name="A", change_reason="r",
        )  # fmt: skip
        a.commit()
        # b は古い版1を持ったまま。アプリ側の確認を通るよう、手元の番号も1のまま
        with pytest.raises(ConflictError):
            review.edit_sense(
                b, sid, expected_revision=1, changes={"definition": "B"},
                editor_name="B", change_reason="r",
            )  # fmt: skip
    with factory() as check:
        assert check.get(Sense, sid).definition == "A"  # type: ignore[union-attr]


def test_every_update_appends_revision(db: Session) -> None:
    sense = accepted_sense(db, "架空語", "v1")
    review.edit_sense(
        db, sense.id, expected_revision=1, changes={"definition": "v2"},
        editor_name=None, change_reason="言い回し",
    )  # fmt: skip
    db.commit()
    revs = db.scalars(
        select(Revision).where(Revision.target_id == sense.id).order_by(Revision.revision_number)
    ).all()
    assert [r.revision_number for r in revs] == [1, 2]
    assert [json.loads(r.snapshot_json)["definition"] for r in revs] == ["v1", "v2"]
    assert revs[1].change_reason == "言い回し"
    assert revs[1].editor_name is None  # 表示名は任意


def test_revisions_are_append_only(db: Session) -> None:
    accepted_sense(db, "架空語")
    with pytest.raises((IntegrityError, OperationalError)):
        raw(db, "UPDATE revisions SET change_reason = '改ざん'")


# ---- 物理削除はできない ----


def test_orm_delete_is_forbidden(db: Session) -> None:
    sense = accepted_sense(db, "架空語")
    db.delete(sense.term)
    with pytest.raises(PhysicalDeleteForbidden):
        db.flush()


@pytest.mark.parametrize(
    "table", ["terms", "senses", "evidences", "relations", "revisions", "proposals"]
)
def test_sql_delete_is_forbidden(db: Session, table: str) -> None:
    accepted_sense(db, "架空語")
    accepted_sense(db, "別の架空語")
    first, second = db.scalars(select(Sense).order_by(Sense.created_at)).all()
    db.add(Relation(from_sense_id=first.id, to_sense_id=second.id,
                    relation_type="related", method="human"))  # fmt: skip
    db.commit()
    with pytest.raises((IntegrityError, OperationalError), match="physical delete is forbidden"):
        raw(db, f"DELETE FROM {table}")


def test_archive_instead_of_delete(db: Session) -> None:
    term = accepted_sense(db, "架空語").term
    review.archive_term(
        db, term.id, expected_revision=term.revision_number, editor_name=None,
        change_reason="使われなくなった",
    )  # fmt: skip
    db.commit()
    assert db.get(Term, term.id).status == "archived"  # type: ignore[union-attr]


# ---- 用例の長さ ----


def test_excerpt_too_long_rejected_by_app(db: Session) -> None:
    p = proposals.add_proposal(
        db,
        proposal_type="sense",
        payload={"headword": "架空語", "definition": "定義",
                 "evidences": [evidence("あ" * (EXCERPT_MAX_LEN + 1))]},
        model_name="mock-llm",
        prompt_version="t",
        score=None,
    )  # fmt: skip
    db.flush()
    with pytest.raises(ValidationFailed, match="文字まで"):
        proposals.accept(db, p.id, reviewer=None)


def test_excerpt_too_long_rejected_by_db(db: Session) -> None:
    insert_term(db)
    insert_sense(db, "s1", first_evidence_id="e1")
    with pytest.raises(IntegrityError):
        insert_evidence(db, "e1", "s1", excerpt="あ" * (EXCERPT_MAX_LEN + 1))


def test_unmasked_mail_excerpt_rejected_by_db(db: Session) -> None:
    insert_term(db)
    insert_sense(db, "s1", first_evidence_id="e1")
    with pytest.raises(IntegrityError):
        raw(
            db,
            "INSERT INTO evidences (id, sense_id, source_type, source_ref, excerpt, masked) "
            "VALUES ('e1', 's1', 'mail', 'eml:1', '伏せていない', 0)",
        )


# ---- 日時 ----


def test_datetimes_round_trip_as_utc(db: Session) -> None:
    from datetime import UTC

    sense = accepted_sense(db, "架空語")
    db.expire_all()
    fresh = db.get(Sense, sense.id)
    assert fresh is not None
    assert fresh.created_at.tzinfo is UTC
    # helpers の用例は 2031-04-01T09:00+09:00。UTC では 00:00
    assert fresh.evidences[0].occurred_at == datetime(2031, 4, 1, 0, 0, tzinfo=UTC)


def test_naive_datetime_is_rejected(db: Session) -> None:
    from glossary.db.models import UtcDateTime

    with pytest.raises(ValueError, match="時差"):
        UtcDateTime().process_bind_param(datetime(2031, 1, 1), db.get_bind().dialect)
