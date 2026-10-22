"""画面表示用の読み取り。書き込みはしない。"""

from __future__ import annotations

import difflib
import json
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from glossary.db.models import RELATION_TYPES, Relation, Revision, Sense, Term

PER_PAGE = 20

# 一覧で列ソートに使える列。URL のパラメータはこの名前で受ける
SORTABLE = {"headword": Term.headword, "reading": Term.reading, "status": Term.status}


@dataclass
class TermPage:
    items: list[Term]
    total: int
    page: int
    pages: int


def list_terms(
    session: Session,
    *,
    q: str = "",
    tag: str = "",
    status: str = "",
    page: int = 1,
    sort: str = "headword",
    direction: str = "asc",
) -> TermPage:
    stmt = select(Term)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Term.headword.like(like),
                Term.reading.like(like),
                Term.english.like(like),
                Term.abbreviation.like(like),
            )
        )
    if tag:
        stmt = stmt.where(Term.senses.any(Sense.context_tag == tag))
    # 状態の指定が無いときは archived を隠す。消した扱いのものが一覧に混ざらないように
    stmt = stmt.where(Term.status == status) if status else stmt.where(Term.status != "archived")
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    pages = max(1, -(-total // PER_PAGE))
    page = min(max(1, page), pages)
    # ソート列の指定が不正なときは既定（見出し）に戻す。第2キーを見出しにして並びを安定させる
    column = SORTABLE.get(sort, Term.headword)
    order = column.desc() if direction == "desc" else column.asc().nulls_last()
    items = session.scalars(
        stmt.order_by(order, Term.headword.asc()).offset((page - 1) * PER_PAGE).limit(PER_PAGE)
    ).all()
    return TermPage(list(items), total, page, pages)


def context_tags(session: Session) -> list[str]:
    rows = session.scalars(
        select(Sense.context_tag).where(Sense.context_tag.is_not(None)).distinct()
    ).all()
    return sorted(t for t in rows if t)


@dataclass
class RelatedItem:
    headword: str
    term_id: str
    score: float | None
    method: str


@dataclass
class TermDetail:
    term: Term
    senses: list[Sense]
    # relation_type → 関連語。confused_with は画面で目立たせるので別に取り出せるようにしておく
    relations: dict[str, list[RelatedItem]] = field(default_factory=dict)


def term_detail(session: Session, term_id: str) -> TermDetail | None:
    term = session.get(Term, term_id)
    if term is None:
        return None
    senses = list(
        session.scalars(
            select(Sense)
            .where(Sense.term_id == term_id)
            .options(selectinload(Sense.evidences))
            .order_by(Sense.created_at)
        ).all()
    )
    ids = [s.id for s in senses]
    grouped: dict[str, list[RelatedItem]] = {t: [] for t in RELATION_TYPES}
    if ids:
        rels = session.scalars(
            select(Relation)
            .where(or_(Relation.from_sense_id.in_(ids), Relation.to_sense_id.in_(ids)))
            .options(selectinload(Relation.from_sense), selectinload(Relation.to_sense))
        ).all()
        for r in rels:
            other = r.to_sense if r.from_sense_id in ids else r.from_sense
            other_term = session.get(Term, other.term_id)
            assert other_term is not None
            grouped[r.relation_type].append(
                RelatedItem(other_term.headword, other_term.id, r.score, r.method)
            )
    return TermDetail(term, senses, {k: v for k, v in grouped.items() if v})


@dataclass
class HistoryEntry:
    revision: Revision
    snapshot: dict[str, Any]
    diff: list[str]


def _lines(snap: dict[str, Any]) -> list[str]:
    # 毎回変わる時刻と版番号は差分から外す。人が見たいのは中身の変化
    skip = {"updated_at", "revision_number"}
    return [f"{k}: {snap[k]}" for k in sorted(snap) if k not in skip]


def diff_lines(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    return list(difflib.unified_diff(_lines(before), _lines(after), lineterm="", n=0))[2:]


def history(session: Session, target_type: str, target_id: str) -> list[HistoryEntry]:
    revs = session.scalars(
        select(Revision)
        .where(Revision.target_type == target_type, Revision.target_id == target_id)
        .order_by(Revision.revision_number)
    ).all()
    out: list[HistoryEntry] = []
    prev: dict[str, Any] = {}
    for r in revs:
        snap = json.loads(r.snapshot_json)
        out.append(HistoryEntry(r, snap, diff_lines(prev, snap)))
        prev = snap
    return out


EXPORT_HEADER = [
    "見出し", "読み", "英語", "略語", "用語の状態", "語義番号", "定義", "適用範囲",
    "文脈タグ", "語義の状態", "用例", "出典", "関連語",
]  # fmt: skip


def export_rows(session: Session) -> list[list[str]]:
    """用語集を1語義1行で書き出す。アーカイブ済みは外す（消した扱いのものを配らないため）。"""
    rows: list[list[str]] = []
    terms = session.scalars(
        select(Term).where(Term.status != "archived").order_by(Term.headword)
    ).all()
    for term in terms:
        detail = term_detail(session, term.id)
        assert detail is not None
        related = " / ".join(
            f"{r.headword}（{t}）" for t, items in detail.relations.items() for r in items
        )
        for i, s in enumerate(detail.senses, 1):
            rows.append(
                [
                    term.headword, term.reading or "", term.english or "",
                    term.abbreviation or "", term.status, str(i), s.definition,
                    s.scope_note or "", s.context_tag or "", s.status,
                    " / ".join(e.excerpt for e in s.evidences),
                    " / ".join(e.source_ref for e in s.evidences), related,
                ]
            )  # fmt: skip
    return rows
