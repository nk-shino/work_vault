"""レビュー画面からの編集。語義を直接書き換えられるのは提案の受理とここだけ。"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from glossary.db.guards import edit_context, snapshot
from glossary.db.models import Sense, Term
from glossary.domain import sense_writer
from glossary.domain.errors import ConflictError, NotFound, ValidationFailed


def edit_sense(
    session: Session,
    sense_id: str,
    *,
    expected_revision: int,
    changes: dict[str, Any],
    editor_name: str | None,
    change_reason: str,
) -> Sense:
    sense = session.get(Sense, sense_id)
    if sense is None:
        raise NotFound(f"語義が無い: {sense_id}")
    try:
        with edit_context(session, editor_name, change_reason):
            return sense_writer.update_sense(
                session, sense, expected_revision=expected_revision, changes=changes
            )
    except StaleDataError:
        # 版の確認とUPDATEの間に割り込まれた場合。DB の WHERE revision_number で弾かれている
        session.rollback()
        current = session.get(Sense, sense_id)
        assert current is not None
        raise ConflictError(snapshot(current), changes, expected_revision) from None


def archive_term(
    session: Session,
    term_id: str,
    *,
    expected_revision: int,
    editor_name: str | None,
    change_reason: str,
) -> Term:
    """用語を消す代わりに archived にする。物理削除の経路は作らない。"""
    term = session.get(Term, term_id)
    if term is None:
        raise NotFound(f"用語が無い: {term_id}")
    if term.status == "archived":
        raise ValidationFailed("既にアーカイブ済み")
    if term.revision_number != expected_revision:
        raise ConflictError(snapshot(term), {"status": "archived"}, expected_revision)
    with edit_context(session, editor_name, change_reason):
        term.status = "archived"
        session.flush()
    return term


TERM_EDITABLE = ("headword", "reading", "english", "abbreviation", "status")


def edit_term(
    session: Session,
    term_id: str,
    *,
    expected_revision: int,
    changes: dict[str, Any],
    change_reason: str,
) -> Term:
    """見出し・読み・英語・略語・状態を直す。アーカイブは archive_term から（理由を分けて残すため）。"""
    term = session.get(Term, term_id)
    if term is None:
        raise NotFound(f"用語が無い: {term_id}")
    if set(changes) - set(TERM_EDITABLE):
        raise ValidationFailed(f"編集できない項目: {sorted(set(changes) - set(TERM_EDITABLE))}")
    if not str(changes.get("headword", term.headword)).strip():
        raise ValidationFailed("見出し語は空にできない")
    if changes.get("status") not in (None, "draft", "active", "disputed"):
        raise ValidationFailed("状態は 草案・有効・係争中 のいずれか（アーカイブは専用の操作で）")
    if term.revision_number != expected_revision:
        raise ConflictError(snapshot(term), changes, expected_revision)
    try:
        with edit_context(session, None, change_reason):
            for key, value in changes.items():
                setattr(term, key, value)
            session.flush()
    except StaleDataError:
        session.rollback()
        current = session.get(Term, term_id)
        assert current is not None
        raise ConflictError(snapshot(current), changes, expected_revision) from None
    return term
