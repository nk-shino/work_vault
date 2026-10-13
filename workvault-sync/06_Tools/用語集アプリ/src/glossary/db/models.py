"""ORM モデル。

スキーマの正本は Alembic のマイグレーション（migrations/versions）で、ここはその写し。
制約のうち DB でしか書けないもの（削除禁止トリガー、語義→用例の遅延外部キー）は
マイグレーション側にだけある。ここで create_all してもそれらは付かないので、
DB は必ず `alembic upgrade head` で作る。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

# 用例は「定義を裏付ける短い抜粋」であって本文ではない。長さで本文の丸写しを止める
EXCERPT_MAX_LEN = 400

TERM_STATUSES = ("draft", "active", "disputed", "archived")
SENSE_STATUSES = ("ai_draft", "needs_review", "confirmed", "disputed", "rejected")
SENSE_SOURCE_TYPES = ("ai", "human")
EVIDENCE_SOURCE_TYPES = ("mail", "doc", "manual")
RELATION_TYPES = ("related", "synonym", "abbrev_of", "broader", "narrower", "confused_with")
RELATION_METHODS = ("cooccurrence", "embedding", "llm", "human")
# evidence：登録済みの語義に用例を足す提案（自動判定が作る）
PROPOSAL_TYPES = ("sense", "relation", "evidence")
# 語義を誰が採用したか。確定（掲載）と、人が中身を確かめたかどうかは別物なので分けて持つ
ADOPTED_BY = ("auto", "human")
ACCURACY_VALUES = ("correct", "needs_fix", "unsure")
USEFULNESS_VALUES = ("useful", "not_useful")
PROPOSAL_STATUSES = ("pending", "accepted", "rejected")
REVISION_TARGETS = ("term", "sense")


def new_id() -> str:
    return uuid.uuid4().hex


def now() -> datetime:
    return datetime.now(UTC)


def in_list(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class UtcDateTime(TypeDecorator[datetime]):
    """日時は UTC に揃えて保存し、読むときに UTC を付け直す。

    SQLite はタイムゾーンを保存しないので、そのままだと「保存前は +09:00、読み直すと時差なし」
    になり、同じ値なのに履歴の差分に出てくる。時差の無い値は受け付けない（どの時刻か決められない）。
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError(f"時差の無い日時は保存しない: {value!r}")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        return None if value is None else value.replace(tzinfo=UTC)


class Base(DeclarativeBase):
    pass


class Term(Base):
    __tablename__ = "terms"
    __table_args__ = (CheckConstraint(in_list("status", TERM_STATUSES), name="ck_terms_status"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    headword: Mapped[str] = mapped_column(String(200))
    reading: Mapped[str | None] = mapped_column(String(200))
    english: Mapped[str | None] = mapped_column(String(200))
    abbreviation: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="draft")
    revision_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=now, onupdate=now)

    senses: Mapped[list[Sense]] = relationship(back_populates="term", order_by="Sense.created_at")

    # 楽観ロック。UPDATE 時に WHERE revision_number = 旧値 が付き、食い違えば StaleDataError になる
    __mapper_args__ = {"version_id_col": revision_number}


class Sense(Base):
    __tablename__ = "senses"
    __table_args__ = (
        CheckConstraint(in_list("status", SENSE_STATUSES), name="ck_senses_status"),
        CheckConstraint(in_list("source_type", SENSE_SOURCE_TYPES), name="ck_senses_source_type"),
        CheckConstraint("length(trim(definition)) > 0", name="ck_senses_definition"),
        CheckConstraint(in_list("adopted_by", ADOPTED_BY), name="ck_senses_adopted_by"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    term_id: Mapped[str] = mapped_column(ForeignKey("terms.id"))
    # 最初の用例。DB 側では (first_evidence_id, id) → evidences(id, sense_id) の遅延外部キーで、
    # 「この語義自身の用例が1件以上ある」ことをコミット時に確かめる（マイグレーション参照）
    first_evidence_id: Mapped[str] = mapped_column(String(32))
    definition: Mapped[str] = mapped_column(Text)
    scope_note: Mapped[str | None] = mapped_column(Text)
    context_tag: Mapped[str | None] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(10))
    confidence: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="needs_review")
    adopted_by: Mapped[str] = mapped_column(String(10), default="human")
    revision_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=now)
    updated_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=now, onupdate=now)

    term: Mapped[Term] = relationship(back_populates="senses")
    evidences: Mapped[list[Evidence]] = relationship(
        back_populates="sense", order_by="Evidence.occurred_at"
    )

    __mapper_args__ = {"version_id_col": revision_number}


class Evidence(Base):
    __tablename__ = "evidences"
    __table_args__ = (
        CheckConstraint(in_list("source_type", EVIDENCE_SOURCE_TYPES), name="ck_evid_source_type"),
        CheckConstraint(f"length(excerpt) <= {EXCERPT_MAX_LEN}", name="ck_evid_excerpt_len"),
        CheckConstraint("source_type <> 'mail' OR masked = 1", name="ck_evid_mail_masked"),
        UniqueConstraint("id", "sense_id", name="uq_evid_id_sense"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    sense_id: Mapped[str] = mapped_column(ForeignKey("senses.id"))
    source_type: Mapped[str] = mapped_column(String(10))
    source_ref: Mapped[str] = mapped_column(String(300))
    excerpt: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    masked: Mapped[bool] = mapped_column(Boolean)

    sense: Mapped[Sense] = relationship(back_populates="evidences")


class Relation(Base):
    __tablename__ = "relations"
    __table_args__ = (
        CheckConstraint("from_sense_id <> to_sense_id", name="ck_rel_not_self"),
        CheckConstraint(in_list("relation_type", RELATION_TYPES), name="ck_rel_type"),
        CheckConstraint(in_list("method", RELATION_METHODS), name="ck_rel_method"),
        UniqueConstraint("from_sense_id", "to_sense_id", "relation_type", name="uq_rel"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    from_sense_id: Mapped[str] = mapped_column(ForeignKey("senses.id"))
    to_sense_id: Mapped[str] = mapped_column(ForeignKey("senses.id"))
    relation_type: Mapped[str] = mapped_column(String(20))
    score: Mapped[float | None] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=now)

    from_sense: Mapped[Sense] = relationship(foreign_keys=[from_sense_id])
    to_sense: Mapped[Sense] = relationship(foreign_keys=[to_sense_id])


class Revision(Base):
    __tablename__ = "revisions"
    __table_args__ = (
        CheckConstraint(in_list("target_type", REVISION_TARGETS), name="ck_rev_target"),
        CheckConstraint("length(trim(change_reason)) > 0", name="ck_rev_reason"),
        UniqueConstraint("target_type", "target_id", "revision_number", name="uq_rev"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    target_type: Mapped[str] = mapped_column(String(10))
    target_id: Mapped[str] = mapped_column(String(32))
    revision_number: Mapped[int] = mapped_column(Integer)
    snapshot_json: Mapped[str] = mapped_column(Text)
    editor_name: Mapped[str | None] = mapped_column(String(100))
    change_reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=now)


class Proposal(Base):
    __tablename__ = "proposals"
    __table_args__ = (
        CheckConstraint(in_list("proposal_type", PROPOSAL_TYPES), name="ck_prop_type"),
        CheckConstraint(in_list("status", PROPOSAL_STATUSES), name="ck_prop_status"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    proposal_type: Mapped[str] = mapped_column(String(20))
    payload_json: Mapped[str] = mapped_column(Text)
    model_name: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(50))
    score: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reviewed_by: Mapped[str | None] = mapped_column(String(100))
    reviewed_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=now)
    # 自動判定がなぜ採用・保留したか。人が保留分を見るときの手がかりにする
    decision_note: Mapped[str | None] = mapped_column(Text)


class Evaluation(Base):
    """登録後の評価。押した時点の語義の版に結び付ける。

    定義が直された後に、旧版への「正しい」を新版の評価として数えないため。
    評価は追記だけで、書き換えも削除もしない（DB のトリガーでも止める）。
    ログインが無いので、誰が押したかは持たない。件数を人数や合意の強さとして見せないこと。
    """

    __tablename__ = "evaluations"
    __table_args__ = (
        CheckConstraint(
            f"accuracy IS NULL OR {in_list('accuracy', ACCURACY_VALUES)}", name="ck_eval_accuracy"
        ),
        CheckConstraint(
            f"usefulness IS NULL OR {in_list('usefulness', USEFULNESS_VALUES)}",
            name="ck_eval_usefulness",
        ),
        CheckConstraint("accuracy IS NOT NULL OR usefulness IS NOT NULL", name="ck_eval_any"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    sense_id: Mapped[str] = mapped_column(ForeignKey("senses.id"))
    sense_revision: Mapped[int] = mapped_column(Integer)
    accuracy: Mapped[str | None] = mapped_column(String(20))
    usefulness: Mapped[str | None] = mapped_column(String(20))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), default=now)
