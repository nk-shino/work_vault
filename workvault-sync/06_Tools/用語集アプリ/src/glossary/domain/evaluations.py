"""登録後の評価と、見直しの一覧。

全件を人が事前に承認する運用をやめた代わりに、登録された語義を読んだ人が
「正しいか」「役に立つか」をその場で押せるようにする。評価は定義を書き換えない。
直すときはレビュー画面（sense_writer）を通す。

ログインが無いので、誰が押したかは分からない。件数は「押された回数」であって、
人数や合意の強さではない。画面でもそう書く。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from glossary.db.models import ACCURACY_VALUES, USEFULNESS_VALUES, Evaluation, Sense, Term
from glossary.domain.errors import NotFound, ValidationFailed

COMMENT_MAX_LEN = 400


def evaluate(
    session: Session,
    sense_id: str,
    *,
    seen_revision: int,
    accuracy: str | None = None,
    usefulness: str | None = None,
    comment: str | None = None,
) -> Evaluation:
    sense = session.get(Sense, sense_id)
    if sense is None:
        raise NotFound(f"語義が無い: {sense_id}")
    if accuracy is None and usefulness is None:
        raise ValidationFailed("評価を選んでください")
    if accuracy is not None and accuracy not in ACCURACY_VALUES:
        raise ValidationFailed(f"正確性の値が不正: {accuracy}")
    if usefulness is not None and usefulness not in USEFULNESS_VALUES:
        raise ValidationFailed(f"有用性の値が不正: {usefulness}")
    # 画面を開いた後に定義が直されていたら、古い定義への評価を新しい版に付けない
    if sense.revision_number != seen_revision:
        raise ValidationFailed("評価している間に定義が更新されました。表示し直してから評価してください")
    text = (comment or "").strip() or None
    if text and len(text) > COMMENT_MAX_LEN:
        raise ValidationFailed(f"理由・修正案は {COMMENT_MAX_LEN} 文字まで")
    ev = Evaluation(
        sense_id=sense.id,
        sense_revision=sense.revision_number,
        accuracy=accuracy,
        usefulness=usefulness,
        comment=text,
    )
    session.add(ev)
    session.flush()
    return ev


@dataclass
class Summary:
    """今の版への評価のまとめ。旧版への評価は数えない（history に残るだけ）。"""

    accuracy: Counter[str] = field(default_factory=Counter)
    usefulness: Counter[str] = field(default_factory=Counter)
    comments: list[Evaluation] = field(default_factory=list)
    older: int = 0  # 旧版への評価の数

    @property
    def unevaluated(self) -> bool:
        return not self.accuracy and not self.usefulness

    @property
    def needs_fix(self) -> bool:
        return self.accuracy["needs_fix"] > 0

    @property
    def split(self) -> bool:
        return self.accuracy["correct"] > 0 and self.accuracy["needs_fix"] > 0

    @property
    def not_useful(self) -> bool:
        return self.usefulness["not_useful"] > 0


def summaries(session: Session, senses: list[Sense]) -> dict[str, Summary]:
    out = {s.id: Summary() for s in senses}
    if not senses:
        return out
    current = {s.id: s.revision_number for s in senses}
    rows = session.scalars(
        select(Evaluation)
        .where(Evaluation.sense_id.in_(list(current)))
        .order_by(Evaluation.created_at.desc())
    ).all()
    for ev in rows:
        sm = out[ev.sense_id]
        if ev.sense_revision != current[ev.sense_id]:
            sm.older += 1
            continue
        if ev.accuracy:
            sm.accuracy[ev.accuracy] += 1
        if ev.usefulness:
            sm.usefulness[ev.usefulness] += 1
        if ev.comment:
            sm.comments.append(ev)
    return out


REVIEW_KINDS = {
    "needs_fix": "「修正が必要」が付いている",
    "split": "「正しい」と「修正が必要」の両方が付いている",
    "not_useful": "「役に立たない」が付いている",
    "auto_unevaluated": "自動採用のまま、まだ誰も評価していない",
    "unevaluated": "まだ誰も評価していない",
}


@dataclass
class ReviewItem:
    sense: Sense
    term: Term
    summary: Summary


def review_queue(session: Session, kind: str) -> list[ReviewItem]:
    """見直しの一覧。問題のありそうなものから人の手を回すため。"""
    if kind not in REVIEW_KINDS:
        raise ValidationFailed(f"見直しの種類が不正: {kind}")
    senses = list(
        session.scalars(
            select(Sense)
            .join(Term)
            .where(Term.status != "archived", Sense.status.not_in(("rejected",)))
            .order_by(Term.headword, Sense.created_at)
        ).all()
    )
    sums = summaries(session, senses)

    def hit(s: Sense) -> bool:
        sm = sums[s.id]
        if kind == "auto_unevaluated":
            return s.adopted_by == "auto" and sm.unevaluated
        return bool(getattr(sm, kind))

    return [ReviewItem(s, s.term, sums[s.id]) for s in senses if hit(s)]


def review_counts(session: Session) -> dict[str, int]:
    return {k: len(review_queue(session, k)) for k in REVIEW_KINDS}
