"""登録後の評価と自動採用

Revision ID: 0002
Revises: 0001

- evaluations：語義の版に結び付けた評価（追記のみ）
- senses.adopted_by：自動で採用したか、人が採用したか
- proposals：用例の追加（evidence）を提案の種類に足し、判定の理由（decision_note）を持たせる
"""

from alembic import op
import sqlalchemy as sa

from glossary.db.models import (
    ACCURACY_VALUES,
    PROPOSAL_STATUSES,
    PROPOSAL_TYPES,
    USEFULNESS_VALUES,
    in_list,
)

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 既にある語義はすべて人が画面で採用したもの。既定値の human がそのまま正しい。
    # ADD COLUMN なら表を作り直さずに済む（senses には遅延外部キーとトリガーがあり、作り直すと面倒）
    op.execute(
        "ALTER TABLE senses ADD COLUMN adopted_by VARCHAR(10) NOT NULL DEFAULT 'human' "
        "CONSTRAINT ck_senses_adopted_by CHECK (adopted_by IN ('auto', 'human'))"
    )

    op.create_table(
        "evaluations",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("sense_id", sa.String(32), sa.ForeignKey("senses.id"), nullable=False),
        sa.Column("sense_revision", sa.Integer, nullable=False),
        sa.Column("accuracy", sa.String(20)),
        sa.Column("usefulness", sa.String(20)),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"accuracy IS NULL OR {in_list('accuracy', ACCURACY_VALUES)}", name="ck_eval_accuracy"
        ),
        sa.CheckConstraint(
            f"usefulness IS NULL OR {in_list('usefulness', USEFULNESS_VALUES)}",
            name="ck_eval_usefulness",
        ),
        sa.CheckConstraint("accuracy IS NOT NULL OR usefulness IS NOT NULL", name="ck_eval_any"),
    )
    op.create_index("ix_evaluations_sense", "evaluations", ["sense_id", "sense_revision"])
    op.execute(
        "CREATE TRIGGER trg_evaluations_no_delete BEFORE DELETE ON evaluations "
        "BEGIN SELECT RAISE(ABORT, 'physical delete is forbidden: evaluations'); END"
    )
    op.execute(
        "CREATE TRIGGER trg_evaluations_no_update BEFORE UPDATE ON evaluations "
        "BEGIN SELECT RAISE(ABORT, 'evaluations are append-only'); END"
    )

    # proposals の種類の CHECK を広げるには、SQLite では表を作り直すしかない。
    # 作り直しの途中で旧表を消すので、削除禁止のトリガーをいったん外して最後に付け直す
    op.execute("DROP TRIGGER trg_proposals_no_delete")
    # copy_from には 0001 時点の定義を渡す。旧表から写す列はこの定義で決まるため、
    # 新しい列（decision_note）はここに入れず、作り直しの中で足す
    old_proposals = sa.Table(
        "proposals",
        sa.MetaData(),
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("proposal_type", sa.String(20), nullable=False),
        sa.Column("payload_json", sa.Text, nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("prompt_version", sa.String(50), nullable=False),
        sa.Column("score", sa.Float),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reviewed_by", sa.String(100)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("proposal_type IN ('sense', 'relation')", name="ck_prop_type"),
        sa.CheckConstraint(in_list("status", PROPOSAL_STATUSES), name="ck_prop_status"),
    )
    with op.batch_alter_table("proposals", copy_from=old_proposals, recreate="always") as b:
        b.add_column(sa.Column("decision_note", sa.Text))
        b.drop_constraint("ck_prop_type", type_="check")
        b.create_check_constraint("ck_prop_type", in_list("proposal_type", PROPOSAL_TYPES))
    op.create_index("ix_proposals_status", "proposals", ["status"])
    op.execute(
        "CREATE TRIGGER trg_proposals_no_delete BEFORE DELETE ON proposals "
        "BEGIN SELECT RAISE(ABORT, 'physical delete is forbidden: proposals'); END"
    )


def downgrade() -> None:
    raise NotImplementedError("downgrade は提供しない（物理削除になるため）")
