"""レビュー画面からの語義の編集。sense_writer を通るもう1つの書き込み経路。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from vbaglossary.db.models import Sense
from vbaglossary.domain import sense_writer
from vbaglossary.domain.errors import NotFound


def edit_sense(
    session: Session, sense_id: str, *, expected_revision: int, text: str, reason: str
) -> Sense:
    sense = session.get(Sense, sense_id)
    if sense is None:
        raise NotFound(f"語義が見つからない: {sense_id}")
    return sense_writer.update_sense(
        session,
        sense,
        expected_revision=expected_revision,
        changes={"text": text},
        reason=reason,
    )
