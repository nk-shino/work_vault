"""読み取り系の集約。画面と統計はここから取り、書き込みは domain の他モジュールへ。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from vbaglossary.db.models import (
    Book,
    Evaluation,
    History,
    Module,
    Procedure,
    Proposal,
    Sense,
)


@dataclass
class Stats:
    procedures: int = 0
    senses: int = 0
    open_proposals: int = 0
    held_proposals: int = 0
    needs_review: int = 0
    modules: int = 0
    books: int = 0
    tag_counts: dict[str, int] = field(default_factory=dict)


def stats(session: Session) -> Stats:
    s = Stats()
    s.books = session.scalar(select(func.count()).select_from(Book)) or 0
    s.modules = session.scalar(select(func.count()).select_from(Module)) or 0
    s.procedures = (
        session.scalar(
            select(func.count()).select_from(Procedure).where(Procedure.archived.is_(False))
        )
        or 0
    )
    s.senses = (
        session.scalar(select(func.count()).select_from(Sense).where(Sense.archived.is_(False)))
        or 0
    )
    s.open_proposals = (
        session.scalar(
            select(func.count())
            .select_from(Proposal)
            .where(Proposal.decided_at.is_(None), Proposal.state.in_(("new", "update")))
        )
        or 0
    )
    s.held_proposals = (
        session.scalar(
            select(func.count())
            .select_from(Proposal)
            .where(Proposal.decided_at.is_(None), Proposal.state == "hold")
        )
        or 0
    )
    s.needs_review = len(review_list(session))
    tag_counts: dict[str, int] = {}
    for (tags_json,) in session.execute(
        select(Procedure.tags_json).where(Procedure.archived.is_(False))
    ):
        for tag in json.loads(tags_json):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    s.tag_counts = dict(sorted(tag_counts.items(), key=lambda kv: -kv[1]))
    return s


def _procedure_rows(session: Session) -> list[dict[str, Any]]:
    rows = session.execute(
        select(Procedure, Module, Book)
        .join(Module, Procedure.module_id == Module.id)
        .join(Book, Module.book_id == Book.id)
        .where(Procedure.archived.is_(False))
        .order_by(Book.name, Module.name, Procedure.start_line)
    ).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "kind": p.kind,
            "access": p.access,
            "signature": p.signature,
            "returns": p.returns,
            "line_count": p.line_count,
            "start_line": p.start_line,
            "tags": json.loads(p.tags_json),
            "module_name": m.name,
            "module_id": m.id,
            "book_name": b.name,
            "source_key": p.source_key,
        }
        for p, m, b in rows
    ]


def list_procedures(
    session: Session,
    *,
    q: str = "",
    kind: str = "",
    module_id: str = "",
    tag: str = "",
    learned: str = "",
) -> list[dict[str, Any]]:
    rows = _procedure_rows(session)
    sense_by_proc: dict[str, int] = {}
    for proc_id, in session.execute(
        select(Sense.procedure_id).where(Sense.archived.is_(False))
    ):
        sense_by_proc[proc_id] = sense_by_proc.get(proc_id, 0) + 1
    word = q.strip().lower()
    out = []
    for row in rows:
        row["sense_count"] = sense_by_proc.get(row["id"], 0)
        if word and word not in (
            row["name"] + row["signature"] + row["module_name"]
        ).lower():
            continue
        if kind and not row["kind"].startswith(kind):
            continue
        if module_id and row["module_id"] != module_id:
            continue
        if tag and tag not in row["tags"]:
            continue
        if learned == "yes" and row["sense_count"] == 0:
            continue
        if learned == "no" and row["sense_count"] > 0:
            continue
        out.append(row)
    return out


def get_procedure(session: Session, procedure_id: str) -> dict[str, Any] | None:
    row = session.execute(
        select(Procedure, Module, Book)
        .join(Module, Procedure.module_id == Module.id)
        .join(Book, Module.book_id == Book.id)
        .where(Procedure.id == procedure_id)
    ).first()
    if row is None:
        return None
    p, m, b = row
    senses = session.scalars(
        select(Sense)
        .where(Sense.procedure_id == p.id, Sense.archived.is_(False))
        .order_by(Sense.created_at)
    ).all()
    open_proposals = session.scalars(
        select(Proposal)
        .where(Proposal.procedure_id == p.id, Proposal.decided_at.is_(None))
        .order_by(Proposal.created_at)
    ).all()
    same_name = session.scalars(
        select(Procedure).where(
            Procedure.name == p.name,
            Procedure.id != p.id,
            Procedure.archived.is_(False),
        )
    ).all()
    return {
        "id": p.id,
        "name": p.name,
        "kind": p.kind,
        "access": p.access,
        "signature": p.signature,
        "params": json.loads(p.params_json),
        "returns": p.returns,
        "start_line": p.start_line,
        "end_line": p.end_line,
        "line_count": p.line_count,
        "calls": json.loads(p.calls_json),
        "called_by": json.loads(p.called_by_json),
        "tags": json.loads(p.tags_json),
        "archived": p.archived,
        "module_id": m.id,
        "module_name": m.name,
        "module_kind": m.kind,
        "file_name": m.file_name,
        "book_id": b.id,
        "book_name": b.name,
        "sha256": b.sha256,
        "senses": senses,
        "open_proposals": open_proposals,
        "same_name": [{"id": x.id, "module_name": None} for x in same_name],
    }


def list_proposals(session: Session, *, state: str = "") -> list[dict[str, Any]]:
    stmt = (
        select(Proposal, Procedure, Module)
        .join(Procedure, Proposal.procedure_id == Procedure.id)
        .join(Module, Procedure.module_id == Module.id)
        .order_by(Proposal.created_at)
    )
    if state:
        stmt = stmt.where(Proposal.state == state)
    else:
        stmt = stmt.where(Proposal.decided_at.is_(None))
    return [
        {
            "id": pr.id,
            "state": pr.state,
            "draft_text": pr.draft_text,
            "draft_source": pr.draft_source,
            "excerpt": pr.excerpt,
            "reason": pr.reason,
            "created_at": pr.created_at,
            "procedure_id": p.id,
            "procedure_name": p.name,
            "signature": p.signature,
            "module_name": m.name,
        }
        for pr, p, m in session.execute(stmt).all()
    ]


def review_list(session: Session) -> list[dict[str, Any]]:
    """見直し対象: 現行版に「修正が必要」の評価がある語義、または同じ版で意見が割れている語義。"""
    senses = session.scalars(
        select(Sense).where(Sense.archived.is_(False)).order_by(Sense.updated_at.desc())
    ).all()
    out: list[dict[str, Any]] = []
    for sense in senses:
        evals = session.scalars(
            select(Evaluation).where(
                Evaluation.sense_id == sense.id, Evaluation.sense_version == sense.version
            )
        ).all()
        if not evals:
            continue
        accuracy = {e.accuracy for e in evals}
        needs_fix = "needs_fix" in accuracy
        disputed = "needs_fix" in accuracy and "correct" in accuracy
        if not (needs_fix or disputed):
            continue
        out.append(
            {
                "sense_id": sense.id,
                "text": sense.text,
                "version": sense.version,
                "needs_fix": needs_fix,
                "disputed": disputed,
                "evaluations": evals,
            }
        )
    return out


def history_for(session: Session, entity: str, entity_id: str) -> list[History]:
    return list(
        session.scalars(
            select(History)
            .where(History.entity == entity, History.entity_id == entity_id)
            .order_by(History.created_at.desc())
        )
    )
