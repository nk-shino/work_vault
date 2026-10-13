"""テスト用の小道具。語義は正規の入口（提案の受理）からしか作れないので、それを通す。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from glossary.db.models import Sense, Term
from glossary.domain import proposals


def evidence(excerpt: str = "架空語が出てくる用例。", ref: str = "eml:0001.eml") -> dict[str, object]:
    return {
        "source_type": "mail",
        "source_ref": ref,
        "excerpt": excerpt,
        "occurred_at": "2031-04-01T09:00:00+09:00",
        "masked": True,
    }


def accepted_sense(db: Session, headword: str, definition: str = "架空の定義。") -> Sense:
    p = proposals.add_proposal(
        db,
        proposal_type="sense",
        payload={
            "headword": headword,
            "definition": definition,
            "context_tag": "その他",
            "confidence": 0.5,
            "evidences": [evidence()],
        },
        model_name="mock-llm",
        prompt_version="test",
        score=1.0,
    )
    db.flush()
    proposals.accept(db, p.id, reviewer="テスト")
    db.commit()
    sense = db.scalars(select(Sense).join(Term).where(Term.headword == headword)).first()
    assert sense is not None
    return sense
