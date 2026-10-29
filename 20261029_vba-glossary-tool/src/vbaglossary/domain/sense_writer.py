"""語義（senses）へ書き込む唯一の場所。

呼んでよいのは domain/proposals.py（提案の受理）と domain/review.py（語義の編集）だけ。
それ以外から書こうとすると guards の before_flush で止まる。
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from vbaglossary.db.guards import sense_write_scope
from vbaglossary.db.models import (
    EXCERPT_MAX_LEN,
    SENSE_SOURCES,
    Evidence,
    Procedure,
    Sense,
    new_id,
)
from vbaglossary.domain.errors import ConflictError, ValidationFailed

EDITABLE_FIELDS = ("text",)


@dataclass(frozen=True)
class EvidenceInput:
    source_key: str
    excerpt: str
    masked: bool


def _check_evidences(evidences: list[EvidenceInput]) -> None:
    if not evidences:
        raise ValidationFailed("用例が1件も無い語義は保存できない")
    for ev in evidences:
        if not ev.excerpt.strip():
            raise ValidationFailed("空の用例は保存できない")
        if len(ev.excerpt) > EXCERPT_MAX_LEN:
            raise ValidationFailed(f"用例は {EXCERPT_MAX_LEN} 文字まで（{len(ev.excerpt)} 文字）")
        if not ev.source_key.strip():
            raise ValidationFailed("出典キーの無い用例は保存できない")


def create_sense(
    session: Session,
    procedure: Procedure,
    *,
    text: str,
    evidences: list[EvidenceInput],
    source: str = "user",
    adopted_by: str = "human",
) -> Sense:
    if not text.strip():
        raise ValidationFailed("語義は空にできない")
    if source not in SENSE_SOURCES:
        raise ValidationFailed(f"語義の出所が不正: {source}")
    if procedure.archived:
        raise ValidationFailed("無効化したプロシージャには語義を書けない")
    _check_evidences(evidences)
    ev_ids = [new_id("e") for _ in evidences]
    with sense_write_scope():
        sense = Sense(
            id=new_id("s"),
            procedure_id=procedure.id,
            first_evidence_id=ev_ids[0],
            text=text.strip(),
            source=source,
            adopted_by=adopted_by,
        )
        session.add(sense)
        session.flush()
        for ev_id, ev in zip(ev_ids, evidences, strict=True):
            session.add(
                Evidence(
                    id=ev_id,
                    sense_id=sense.id,
                    excerpt=ev.excerpt.strip(),
                    source_key=ev.source_key,
                    masked=ev.masked,
                )
            )
        session.flush()
    return sense


def update_sense(
    session: Session,
    sense: Sense,
    *,
    expected_revision: int,
    changes: dict[str, str],
    reason: str,
) -> Sense:
    unknown = set(changes) - set(EDITABLE_FIELDS)
    if unknown:
        raise ValidationFailed(f"編集できない項目: {sorted(unknown)}")
    if not reason.strip():
        raise ValidationFailed("語義の更新には理由が必須")
    if sense.version != expected_revision:
        raise ConflictError(
            {"id": sense.id, "text": sense.text, "version": sense.version},
            changes,
            expected_revision,
        )
    with sense_write_scope():
        for key, value in changes.items():
            setattr(sense, key, value.strip())
        sense.last_change_reason = reason.strip()
        session.flush()
    return sense
