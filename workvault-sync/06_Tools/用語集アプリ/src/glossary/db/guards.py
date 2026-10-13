"""アプリケーション層の書き込みガード。DB 側の制約と二重にかける。

DB 側だけだと、どのコードが書いたかを区別できない（語義への書き込み経路の制限）。
アプリ側だけだと、SQL を直接叩かれたら素通りする（削除禁止・用例必須）。
なので両方に置き、片方が抜けてももう片方で止まるようにする。
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from typing import Any

from sqlalchemy import event, insert
from sqlalchemy.orm import Session, sessionmaker

from glossary.db.models import Revision, Sense, Term, new_id, now

# 語義への書き込みを許可している間だけ True になる。
# sense_write_scope を使ってよいのは domain/sense_writer.py だけ（tests/test_write_paths.py で検査）
_SENSE_WRITE_ALLOWED: ContextVar[bool] = ContextVar("sense_write_allowed", default=False)
EDIT_CONTEXT_KEY = "edit_context"


class PhysicalDeleteForbidden(RuntimeError):
    pass


class SenseWriteForbidden(RuntimeError):
    pass


class MissingChangeReason(ValueError):
    pass


@contextmanager
def sense_write_scope() -> Iterator[None]:
    token = _SENSE_WRITE_ALLOWED.set(True)
    try:
        yield
    finally:
        _SENSE_WRITE_ALLOWED.reset(token)


@contextmanager
def edit_context(session: Session, editor_name: str | None, change_reason: str) -> Iterator[None]:
    """用語・語義を変えるときは、誰が・なぜを必ずこの中で指定する。履歴にそのまま残る。"""
    if not change_reason or not change_reason.strip():
        raise MissingChangeReason("編集理由は必須")
    session.info[EDIT_CONTEXT_KEY] = ((editor_name or "").strip() or None, change_reason.strip())
    try:
        yield
    finally:
        session.info.pop(EDIT_CONTEXT_KEY, None)


def snapshot(obj: Term | Sense) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in obj.__table__.columns:
        value = getattr(obj, col.key)
        out[col.key] = value.isoformat() if isinstance(value, datetime) else value
    return out


def _versioned(session: Session) -> list[Term | Sense]:
    objs: list[Term | Sense] = [o for o in session.new if isinstance(o, Term | Sense)]
    # 用例を足しただけ（コレクションの変化）では語義の行は UPDATE されず版も上がらないので、数えない
    objs += [
        o
        for o in session.dirty
        if isinstance(o, Term | Sense) and session.is_modified(o, include_collections=False)
    ]
    return objs


def _before_flush(session: Session, _ctx: Any, _instances: Any) -> None:
    if session.deleted:
        raise PhysicalDeleteForbidden("物理削除はしない。status を archived にすること")
    changed = _versioned(session)
    if any(isinstance(o, Sense) for o in changed) and not _SENSE_WRITE_ALLOWED.get():
        raise SenseWriteForbidden("語義は提案の受理かレビュー画面からしか書き込めない")
    if changed and EDIT_CONTEXT_KEY not in session.info:
        raise MissingChangeReason("用語・語義の変更は edit_context の中で行うこと")
    # after_flush では new / dirty の区別が消えるので、ここで対象を控えておく
    session.info["_pending_revisions"] = changed


def _after_flush(session: Session, _ctx: Any) -> None:
    targets: list[Term | Sense] = session.info.pop("_pending_revisions", [])
    if not targets:
        return
    editor, reason = session.info[EDIT_CONTEXT_KEY]
    rows = [
        {
            "id": new_id(),
            "target_type": "term" if isinstance(o, Term) else "sense",
            "target_id": o.id,
            # version_id_col により、ここでは更新後の番号になっている
            "revision_number": o.revision_number,
            "snapshot_json": json.dumps(snapshot(o), ensure_ascii=False, sort_keys=True),
            "editor_name": editor,
            "change_reason": reason,
            "created_at": now(),
        }
        for o in targets
    ]
    session.connection().execute(insert(Revision), rows)


def install_guards(factory: sessionmaker[Session]) -> None:
    event.listen(factory, "before_flush", _before_flush)
    event.listen(factory, "after_flush", _after_flush)
