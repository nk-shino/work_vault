"""提案の作成と受理。受理は sense_writer を通る書き込み経路の1つ。

もう1つは review.py（語義の編集）。自動採用は行わない（config/adoption.yaml の
auto_adopt は既定 false）。解析は提案を積むだけで、語義は人が確かめて受理する。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from vbaglossary.db.guards import change_reason
from vbaglossary.db.models import History, Procedure, Proposal, Sense, new_id
from vbaglossary.domain import sense_writer
from vbaglossary.domain.errors import NotFound, ValidationFailed
from vbaglossary.domain.sense_writer import EvidenceInput

OPEN_STATES = ("new", "update", "hold")


def add_proposal(
    session: Session,
    procedure: Procedure,
    *,
    state: str,
    draft_text: str,
    excerpt: str,
    draft_source: str = "auto",
    reason: str | None = None,
) -> Proposal | None:
    """提案を積む。同じ source_key の未処理提案があれば内容を差し替え、同一内容なら何もしない。"""
    if state not in OPEN_STATES:
        raise ValidationFailed(f"提案の状態が不正: {state}")
    if not draft_text.strip() or not excerpt.strip():
        raise ValidationFailed("語義ドラフトと用例が空の提案は作れない")
    open_proposal = session.scalars(
        select(Proposal).where(
            Proposal.source_key == procedure.source_key,
            Proposal.decided_at.is_(None),
        )
    ).first()
    if open_proposal is not None:
        if (
            open_proposal.state == state
            and open_proposal.draft_text == draft_text.strip()
            and open_proposal.excerpt == excerpt.strip()
            and open_proposal.draft_source == draft_source
        ):
            return None
        with change_reason("再解析により提案の内容を差し替え"):
            open_proposal.state = state
            open_proposal.draft_text = draft_text.strip()
            open_proposal.draft_source = draft_source
            open_proposal.excerpt = excerpt.strip()
            open_proposal.reason = reason
            session.flush()
        return open_proposal
    proposal = Proposal(
        id=new_id("pr"),
        procedure_id=procedure.id,
        state=state,
        draft_text=draft_text.strip(),
        draft_source=draft_source,
        excerpt=excerpt.strip(),
        reason=reason,
        source_key=procedure.source_key,
    )
    session.add(proposal)
    session.flush()
    return proposal


def accept(
    session: Session,
    proposal_id: str,
    *,
    text: str | None = None,
    reason: str = "提案どおり受理",
    adopted_by: str = "human",
) -> Sense:
    """提案を受理して語義を確定させる。語義・用例・提案の状態・履歴を同じトランザクションで保存する。"""
    proposal = session.get(Proposal, proposal_id)
    if proposal is None:
        raise NotFound(f"提案が見つからない: {proposal_id}")
    if proposal.decided_at is not None:
        raise ValidationFailed("処理済みの提案は受理できない")
    if proposal.state == "hold":
        raise ValidationFailed("保留の提案はそのまま受理できない。語義を直してから受理する")
    meaning = (text if text is not None else proposal.draft_text).strip()
    if not meaning:
        raise ValidationFailed("空の語義は受理できない")
    procedure = session.get(Procedure, proposal.procedure_id)
    if procedure is None:
        raise NotFound(f"プロシージャが見つからない: {proposal.procedure_id}")
    sense = sense_writer.create_sense(
        session,
        procedure,
        text=meaning,
        evidences=[
            EvidenceInput(source_key=proposal.source_key, excerpt=proposal.excerpt, masked=True)
        ],
        source="comment" if proposal.draft_source == "comment" else "user",
        adopted_by=adopted_by,
    )
    with change_reason(reason):
        proposal.decided_at = datetime.now()
        session.flush()
    session.add(
        History(
            id=new_id("h"),
            entity="senses",
            entity_id=sense.id,
            action="accept",
            reason=reason,
            payload=None,
        )
    )
    session.flush()
    return sense


def reject(session: Session, proposal_id: str, *, reason: str) -> Proposal:
    """提案を見送る。語義は作らない。履歴に理由を残す。"""
    proposal = session.get(Proposal, proposal_id)
    if proposal is None:
        raise NotFound(f"提案が見つからない: {proposal_id}")
    if proposal.decided_at is not None:
        raise ValidationFailed("処理済みの提案は見送れない")
    if not reason.strip():
        raise ValidationFailed("見送る理由が必須")
    with change_reason(f"提案を見送り: {reason.strip()}"):
        proposal.decided_at = datetime.now()
        session.flush()
    return proposal
