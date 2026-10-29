"""baseline: 8表とトリガー（物理削除禁止・履歴追記専用・語義の履歴自動追記・理由必須）

Revision ID: 0001
Revises:
Create Date: 2026-10-29
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NO_DELETE = [
    "books",
    "modules",
    "procedures",
    "senses",
    "evidences",
    "proposals",
    "evaluations",
    "histories",
]


def _triggers() -> None:
    for table in NO_DELETE:
        op.execute(
            f"CREATE TRIGGER trg_{table}_no_delete BEFORE DELETE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '物理削除は禁止（{table}）。archived で無効化すること'); END"
        )
    op.execute(
        "CREATE TRIGGER trg_histories_no_update BEFORE UPDATE ON histories "
        "BEGIN SELECT RAISE(ABORT, '履歴は追記専用'); END"
    )
    op.execute(
        "CREATE TRIGGER trg_evaluations_no_update BEFORE UPDATE ON evaluations "
        "BEGIN SELECT RAISE(ABORT, '評価は追記専用'); END"
    )
    op.execute(
        "CREATE TRIGGER trg_senses_reason BEFORE UPDATE ON senses "
        "WHEN NEW.text <> OLD.text "
        "AND (NEW.last_change_reason IS NULL OR trim(NEW.last_change_reason) = '') "
        "BEGIN SELECT RAISE(ABORT, '語義の更新には理由が必須'); END"
    )
    op.execute(
        "CREATE TRIGGER trg_senses_history AFTER UPDATE ON senses "
        "BEGIN "
        "INSERT INTO histories (id, entity, entity_id, action, reason, payload, created_at) "
        "VALUES ("
        "'h_' || lower(hex(randomblob(6))), 'senses', NEW.id, 'update', "
        "COALESCE(NEW.last_change_reason, ''), "
        "json_object('before', OLD.text, 'after', NEW.text, 'version', NEW.version), "
        "strftime('%Y-%m-%dT%H:%M:%S', 'now', 'localtime')); "
        "END"
    )


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.Text(), nullable=False),
        sa.Column("analyzed_at", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_books_sha256", "books", ["sha256"], unique=False)

    op.create_table(
        "modules",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("book_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False, server_default="standard"),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "name", name="uq_modules_book_name"),
    )
    op.create_index("ix_modules_book_id", "modules", ["book_id"], unique=False)

    op.create_table(
        "procedures",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("module_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("access", sa.Text(), nullable=False, server_default="Public"),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("params_json", sa.Text(), nullable=False, server_default="'[]'"),
        sa.Column("returns", sa.Text(), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("line_count", sa.Integer(), nullable=False),
        sa.Column("calls_json", sa.Text(), nullable=False, server_default="'[]'"),
        sa.Column("called_by_json", sa.Text(), nullable=False, server_default="'[]'"),
        sa.Column("tags_json", sa.Text(), nullable=False, server_default="'[]'"),
        sa.Column("source_key", sa.Text(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("archived IN (0, 1)", name="ck_procedures_archived"),
        sa.UniqueConstraint("source_key"),
    )
    op.create_index("ix_procedures_module_id", "procedures", ["module_id"], unique=False)
    op.create_index("ix_procedures_name", "procedures", ["name"], unique=False)

    op.create_table(
        "senses",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("procedure_id", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False, server_default="user"),
        sa.Column("adopted_by", sa.Text(), nullable=False, server_default="human"),
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("last_change_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("first_evidence_id", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["procedure_id"], ["procedures.id"]),
        sa.ForeignKeyConstraint(
            ["first_evidence_id", "id"],
            ["evidences.id", "evidences.sense_id"],
            name="fk_senses_first_evidence",
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("archived IN (0, 1)", name="ck_senses_archived"),
    )
    op.create_index("ix_senses_procedure_id", "senses", ["procedure_id"], unique=False)

    op.create_table(
        "evidences",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("sense_id", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("source_key", sa.Text(), nullable=False),
        sa.Column("masked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["sense_id"], ["senses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("length(excerpt) <= 400", name="ck_evidences_excerpt_len"),
        sa.CheckConstraint("masked IN (0, 1)", name="ck_evidences_masked"),
    )
    op.create_index("ix_evidences_sense_id", "evidences", ["sense_id"], unique=False)
    op.create_index("uq_evidences_id_sense", "evidences", ["id", "sense_id"], unique=True)

    op.create_table(
        "proposals",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("procedure_id", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, server_default="new"),
        sa.Column("draft_text", sa.Text(), nullable=False),
        sa.Column("draft_source", sa.Text(), nullable=False, server_default="auto"),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("source_key", sa.Text(), nullable=False),
        sa.Column("decided_at", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["procedure_id"], ["procedures.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("state IN ('new', 'update', 'hold')", name="ck_proposals_state"),
    )
    op.create_index("ix_proposals_procedure_id", "proposals", ["procedure_id"], unique=False)
    op.create_index("ix_proposals_source_key", "proposals", ["source_key"], unique=False)
    op.create_index(
        "uq_proposals_open_source_key",
        "proposals",
        ["source_key"],
        unique=True,
        sqlite_where=sa.text("decided_at IS NULL"),
    )

    op.create_table(
        "evaluations",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("sense_id", sa.Text(), nullable=False),
        sa.Column("sense_version", sa.Integer(), nullable=False),
        sa.Column("accuracy", sa.Text(), nullable=False),
        sa.Column("usefulness", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["sense_id"], ["senses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "accuracy IN ('correct', 'needs_fix', 'unsure')", name="ck_evaluations_accuracy"
        ),
        sa.CheckConstraint(
            "usefulness IN ('useful', 'not_useful')", name="ck_evaluations_usefulness"
        ),
    )
    op.create_index("ix_evaluations_sense_id", "evaluations", ["sense_id"], unique=False)

    op.create_table(
        "histories",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("entity", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_histories_entity", "histories", ["entity"], unique=False)
    op.create_index("ix_histories_entity_id", "histories", ["entity_id"], unique=False)

    _triggers()


def downgrade() -> None:
    raise NotImplementedError("downgrade は用意しない（物理削除禁止の方針に同じ）")
