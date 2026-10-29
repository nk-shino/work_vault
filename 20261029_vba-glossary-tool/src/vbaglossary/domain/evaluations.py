"""評価の追記。評価だけで語義は変わらない（追記専用・DB トリガーで書き換えも削除も止まる）。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from vbaglossary.db.models import ACCURACY_VALUES, USEFULNESS_VALUES, Evaluation, Sense, new_id
from vbaglossary.domain.errors import NotFound, ValidationFailed


def evaluate(
    session: Session,
    sense_id: str,
    *,
    seen_version: int,
    accuracy: str,
    usefulness: str,
    reason: str | None = None,
) -> Evaluation:
    sense = session.get(Sense, sense_id)
    if sense is None:
        raise NotFound(f"語義が見つからない: {sense_id}")
    if accuracy not in ACCURACY_VALUES:
        raise ValidationFailed(f"正確性の値が不正: {accuracy}")
    if usefulness not in USEFULNESS_VALUES:
        raise ValidationFailed(f"有用性の値が不正: {usefulness}")
    if sense.version != seen_version:
        raise ValidationFailed(
            f"語義の版が違う（表示時 {seen_version}・現在 {sense.version}）。"
            "再読込してから評価し直すこと"
        )
    evaluation = Evaluation(
        id=new_id("v"),
        sense_id=sense.id,
        sense_version=sense.version,
        accuracy=accuracy,
        usefulness=usefulness,
        reason=(reason or "").strip() or None,
    )
    session.add(evaluation)
    session.flush()
    return evaluation
