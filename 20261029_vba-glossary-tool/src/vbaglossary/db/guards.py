"""アプリ層の書き込みガード。

- 物理削除の全面禁止（DB の BEFORE DELETE トリガーと二重にかかる）
- 語義（Sense）への書き込みは sense_write_scope() の内側だけ。呼んでよいのは
  domain/sense_writer.py だけで、それ以外から書くとここで止まる
- procedures / proposals の作成・更新は after_flush で履歴に自動追記する。
  語義の履歴は DB の AFTER UPDATE トリガーが担当する（二重記録しない）
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from vbaglossary.db.models import History, Procedure, Proposal, Sense, new_id

_sense_write_allowed: ContextVar[bool] = ContextVar("sense_write_allowed", default=False)
_change_reason: ContextVar[str] = ContextVar("change_reason", default="")


class WritePathError(Exception):
    """語義への許可されていない書き込み。"""


class DeletionBlocked(Exception):
    """物理削除の拒否。"""


class ChangeReasonMissing(Exception):
    """更新理由が無い変更の拒否。"""


@contextmanager
def sense_write_scope() -> Iterator[None]:
    token = _sense_write_allowed.set(True)
    try:
        yield
    finally:
        _sense_write_allowed.reset(token)


@contextmanager
def change_reason(reason: str) -> Iterator[None]:
    token = _change_reason.set(reason)
    try:
        yield
    finally:
        _change_reason.reset(token)


def snapshot(sense: Sense) -> dict[str, Any]:
    """競合表示に使う語義の現時点の写し。"""
    return {"id": sense.id, "text": sense.text, "version": sense.version}


def _history(
    session: Session, entity: str, entity_id: str, action: str, reason: str, payload: Any
) -> None:
    session.add(
        History(
            id=new_id("h"),
            entity=entity,
            entity_id=entity_id,
            action=action,
            reason=reason or None,
            payload=json.dumps(payload, ensure_ascii=False) if payload else None,
        )
    )


def _before_flush(session: Session, _flush_context: Any, _instances: Any) -> None:
    if session.deleted:
        raise DeletionBlocked("物理削除は禁止。archived フラグで無効化すること")
    sense_writes = [obj for obj in (*session.new, *session.dirty) if isinstance(obj, Sense)]
    if sense_writes and not _sense_write_allowed.get():
        raise WritePathError("語義への書き込みは sense_writer 経由でのみ行える")


def _after_flush(session: Session, _flush_context: Any) -> None:
    reason = _change_reason.get()
    for obj in session.new:
        if isinstance(obj, Procedure):
            _history(
                session, "procedures", obj.id, "create", reason or "解析",
                {"source_key": obj.source_key, "signature": obj.signature},
            )
        elif isinstance(obj, Proposal):
            _history(
                session, "proposals", obj.id, "create", reason or "解析",
                {"state": obj.state, "source_key": obj.source_key},
            )
    for obj in session.dirty:
        if isinstance(obj, Procedure) and session.is_modified(obj, include_collections=False):
            if not reason:
                raise ChangeReasonMissing("procedures の更新には理由が必須")
            _history(
                session, "procedures", obj.id, "update", reason,
                {
                    "signature": obj.signature,
                    "start_line": obj.start_line,
                    "end_line": obj.end_line,
                },
            )
        elif isinstance(obj, Proposal) and session.is_modified(obj, include_collections=False):
            _history(
                session, "proposals", obj.id, "update", reason or "提案の更新",
                {"state": obj.state, "decided": obj.decided_at is not None},
            )


_registered = False


def register_guards() -> None:
    global _registered
    if _registered:
        return
    event.listen(Session, "before_flush", _before_flush)
    event.listen(Session, "after_flush", _after_flush)
    _registered = True
