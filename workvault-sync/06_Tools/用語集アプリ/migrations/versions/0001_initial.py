"""初期スキーマ

Revision ID: 0001
Revises:
"""

from alembic import op
import sqlalchemy as sa

from glossary.db.models import (
    EVIDENCE_SOURCE_TYPES,
    EXCERPT_MAX_LEN,
    PROPOSAL_STATUSES,
    PROPOSAL_TYPES,
    RELATION_METHODS,
    RELATION_TYPES,
    REVISION_TARGETS,
    SENSE_SOURCE_TYPES,
    SENSE_STATUSES,
    TERM_STATUSES,
    in_list,
)

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TABLES = ("terms", "senses", "evidences", "relations", "revisions", "proposals")


def _ts(name: str, nullable: bool = False) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable)


def upgrade() -> None:
    op.create_table(
        "terms",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("headword", sa.String(200), nullable=False),
        sa.Column("reading", sa.String(200)),
        sa.Column("english", sa.String(200)),
        sa.Column("abbreviation", sa.String(50)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("revision_number", sa.Integer, nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
        sa.CheckConstraint(in_list("status", TERM_STATUSES), name="ck_terms_status"),
    )
    op.create_table(
        "senses",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("term_id", sa.String(32), sa.ForeignKey("terms.id"), nullable=False),
        sa.Column("first_evidence_id", sa.String(32), nullable=False),
        sa.Column("definition", sa.Text, nullable=False),
        sa.Column("scope_note", sa.Text),
        sa.Column("context_tag", sa.String(100)),
        sa.Column("source_type", sa.String(10), nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("revision_number", sa.Integer, nullable=False),
        _ts("created_at"),
        _ts("updated_at"),
        sa.CheckConstraint(in_list("status", SENSE_STATUSES), name="ck_senses_status"),
        sa.CheckConstraint(in_list("source_type", SENSE_SOURCE_TYPES), name="ck_senses_source_type"),
        sa.CheckConstraint("length(trim(definition)) > 0", name="ck_senses_definition"),
        # 用例の無い語義を DB でも拒否する要。
        # 語義は「自分を指す用例」を1件指していなければならず、それをコミット時に確かめる。
        # 語義と用例は互いを参照するので即時検査では入れられない。だから遅延（DEFERRED）にする。
        # SQLite は未作成の表を参照する外部キーを許すのでここに書ける。
        # PostgreSQL へ移すときは evidences 作成後に op.create_foreign_key で付け直すこと。
        sa.ForeignKeyConstraint(
            ["first_evidence_id", "id"],
            ["evidences.id", "evidences.sense_id"],
            name="fk_senses_first_evidence",
            deferrable=True,
            initially="DEFERRED",
        ),
    )
    op.create_table(
        "evidences",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("sense_id", sa.String(32), sa.ForeignKey("senses.id"), nullable=False),
        sa.Column("source_type", sa.String(10), nullable=False),
        sa.Column("source_ref", sa.String(300), nullable=False),
        sa.Column("excerpt", sa.Text, nullable=False),
        _ts("occurred_at", nullable=True),
        sa.Column("masked", sa.Boolean, nullable=False),
        sa.CheckConstraint(in_list("source_type", EVIDENCE_SOURCE_TYPES), name="ck_evid_source_type"),
        sa.CheckConstraint(f"length(excerpt) <= {EXCERPT_MAX_LEN}", name="ck_evid_excerpt_len"),
        sa.CheckConstraint("source_type <> 'mail' OR masked = 1", name="ck_evid_mail_masked"),
        sa.UniqueConstraint("id", "sense_id", name="uq_evid_id_sense"),
    )
    op.create_table(
        "relations",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("from_sense_id", sa.String(32), sa.ForeignKey("senses.id"), nullable=False),
        sa.Column("to_sense_id", sa.String(32), sa.ForeignKey("senses.id"), nullable=False),
        sa.Column("relation_type", sa.String(20), nullable=False),
        sa.Column("score", sa.Float),
        sa.Column("method", sa.String(20), nullable=False),
        _ts("created_at"),
        sa.CheckConstraint("from_sense_id <> to_sense_id", name="ck_rel_not_self"),
        sa.CheckConstraint(in_list("relation_type", RELATION_TYPES), name="ck_rel_type"),
        sa.CheckConstraint(in_list("method", RELATION_METHODS), name="ck_rel_method"),
        sa.UniqueConstraint("from_sense_id", "to_sense_id", "relation_type", name="uq_rel"),
    )
    op.create_table(
        "revisions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("target_type", sa.String(10), nullable=False),
        sa.Column("target_id", sa.String(32), nullable=False),
        sa.Column("revision_number", sa.Integer, nullable=False),
        sa.Column("snapshot_json", sa.Text, nullable=False),
        sa.Column("editor_name", sa.String(100)),
        sa.Column("change_reason", sa.Text, nullable=False),
        _ts("created_at"),
        sa.CheckConstraint(in_list("target_type", REVISION_TARGETS), name="ck_rev_target"),
        sa.CheckConstraint("length(trim(change_reason)) > 0", name="ck_rev_reason"),
        sa.UniqueConstraint("target_type", "target_id", "revision_number", name="uq_rev"),
    )
    op.create_table(
        "proposals",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("proposal_type", sa.String(20), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(50), nullable=False),
        sa.Column("score", sa.Float),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reviewed_by", sa.String(100)),
        _ts("reviewed_at", nullable=True),
        _ts("created_at"),
        sa.CheckConstraint(in_list("proposal_type", PROPOSAL_TYPES), name="ck_prop_type"),
        sa.CheckConstraint(in_list("status", PROPOSAL_STATUSES), name="ck_prop_status"),
    )
    op.create_index("ix_senses_term", "senses", ["term_id"])
    op.create_index("ix_evidences_sense", "evidences", ["sense_id"])
    op.create_index("ix_revisions_target", "revisions", ["target_type", "target_id"])
    op.create_index("ix_proposals_status", "proposals", ["status"])

    # 物理削除の禁止。アプリ側でも止めているが、SQL を直接叩かれた場合の最後の砦
    for table in TABLES:
        op.execute(
            f"CREATE TRIGGER trg_{table}_no_delete BEFORE DELETE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, 'physical delete is forbidden: {table}'); END"
        )
    # 履歴は追記のみ。書き換えられると差分表示と監査の意味が無くなる
    op.execute(
        "CREATE TRIGGER trg_revisions_no_update BEFORE UPDATE ON revisions "
        "BEGIN SELECT RAISE(ABORT, 'revisions are append-only'); END"
    )


def downgrade() -> None:
    # 表の削除は全件の物理削除と同じなので、戻す手段は用意しない。作り直すなら DB ファイルごと退避する
    raise NotImplementedError("downgrade は提供しない（物理削除になるため）")
