"""ORM モデル。

制約とトリガーの正本は migrations/versions/ にある。このファイルは列の対応を
保つだけにする。物理削除は全面禁止で、無効化は archived フラグで行う。
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

EXCERPT_MAX_LEN = 400
PROCEDURE_KINDS = ("Sub", "Function", "Property Get", "Property Let", "Property Set")
PROPOSAL_STATES = ("new", "update", "hold")
ACCURACY_VALUES = ("correct", "needs_fix", "unsure")
USEFULNESS_VALUES = ("useful", "not_useful")
SENSE_SOURCES = ("comment", "user")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _now() -> datetime:
    return datetime.now()


class Base(DeclarativeBase):
    pass


class IsoDateTime(TypeDecorator[datetime]):
    """SQLite の DATETIME を ISO 文字列で保持する（タイムゾーンなし・日本時間を想定）。"""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: datetime | None, _dialect: object) -> str | None:
        return value.isoformat(timespec="seconds") if value else None

    def process_result_value(self, value: str | None, _dialect: object) -> datetime | None:
        return datetime.fromisoformat(value) if value else None


class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    analyzed_at: Mapped[datetime] = mapped_column(IsoDateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(IsoDateTime, nullable=False, default=_now)

    modules: Mapped[list[Module]] = relationship(back_populates="book", viewonly=True)


class Module(Base):
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint("book_id", "name", name="uq_modules_book_name"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False, default="standard")
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(IsoDateTime, nullable=False, default=_now)

    book: Mapped[Book] = relationship(back_populates="modules", viewonly=True)


class Procedure(Base):
    __tablename__ = "procedures"
    __table_args__ = (CheckConstraint("archived IN (0, 1)", name="ck_procedures_archived"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    access: Mapped[str] = mapped_column(Text, nullable=False, default="Public")
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    params_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    returns: Mapped[str | None]
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, nullable=False)
    calls_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    called_by_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    tags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    source_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(IsoDateTime, nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        IsoDateTime, nullable=False, default=_now, onupdate=_now
    )

    module: Mapped[Module] = relationship(viewonly=True)
    senses: Mapped[list[Sense]] = relationship(back_populates="procedure", viewonly=True)

    __mapper_args__ = {"version_id_col": version}


class Sense(Base):
    __tablename__ = "senses"
    __table_args__ = (CheckConstraint("archived IN (0, 1)", name="ck_senses_archived"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    procedure_id: Mapped[str] = mapped_column(ForeignKey("procedures.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="user")
    adopted_by: Mapped[str] = mapped_column(Text, nullable=False, default="human")
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_change_reason: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(IsoDateTime, nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        IsoDateTime, nullable=False, default=_now, onupdate=_now
    )
    first_evidence_id: Mapped[str] = mapped_column(
        ForeignKey(
            "evidences.id",
            use_alter=True,
            name="fk_senses_first_evidence",
            deferrable=True,
            initially="DEFERRED",
        ),
        nullable=False,
    )

    procedure: Mapped[Procedure] = relationship(back_populates="senses", viewonly=True)
    evidences: Mapped[list[Evidence]] = relationship(
        back_populates="sense",
        foreign_keys="Evidence.sense_id",
        primaryjoin="Sense.id == foreign(Evidence.sense_id)",
        order_by="Evidence.created_at",
        viewonly=True,
    )

    __mapper_args__ = {"version_id_col": version}


class Evidence(Base):
    __tablename__ = "evidences"
    __table_args__ = (
        CheckConstraint(
            f"length(excerpt) <= {EXCERPT_MAX_LEN}", name="ck_evidences_excerpt_len"
        ),
        CheckConstraint("masked IN (0, 1)", name="ck_evidences_masked"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    sense_id: Mapped[str] = mapped_column(ForeignKey("senses.id"), nullable=False, index=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    source_key: Mapped[str] = mapped_column(Text, nullable=False)
    masked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(IsoDateTime, nullable=False, default=_now)

    sense: Mapped[Sense] = relationship(
        back_populates="evidences",
        foreign_keys=[sense_id],
        primaryjoin="Sense.id == foreign(Evidence.sense_id)",
        viewonly=True,
    )


class Proposal(Base):
    __tablename__ = "proposals"
    __table_args__ = (
        CheckConstraint(
            "state IN ('new', 'update', 'hold')", name="ck_proposals_state"
        ),
        Index(
            "uq_proposals_open_source_key",
            "source_key",
            unique=True,
            sqlite_where=text("decided_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    procedure_id: Mapped[str] = mapped_column(ForeignKey("procedures.id"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(Text, nullable=False, default="new")
    draft_text: Mapped[str] = mapped_column(Text, nullable=False)
    draft_source: Mapped[str] = mapped_column(Text, nullable=False, default="auto")
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None]
    source_key: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    decided_at: Mapped[datetime | None] = mapped_column(IsoDateTime)
    created_at: Mapped[datetime] = mapped_column(IsoDateTime, nullable=False, default=_now)


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        CheckConstraint(
            "accuracy IN ('correct', 'needs_fix', 'unsure')", name="ck_evaluations_accuracy"
        ),
        CheckConstraint(
            "usefulness IN ('useful', 'not_useful')", name="ck_evaluations_usefulness"
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    sense_id: Mapped[str] = mapped_column(ForeignKey("senses.id"), nullable=False, index=True)
    sense_version: Mapped[int] = mapped_column(Integer, nullable=False)
    accuracy: Mapped[str] = mapped_column(Text, nullable=False)
    usefulness: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(IsoDateTime, nullable=False, default=_now)


class History(Base):
    __tablename__ = "histories"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    entity: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None]
    payload: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(IsoDateTime, nullable=False, default=_now)
