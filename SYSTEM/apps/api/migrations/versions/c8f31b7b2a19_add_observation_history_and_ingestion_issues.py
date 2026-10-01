"""add observation history and ingestion issues

Revision ID: c8f31b7b2a19
Revises: 91d6c2fe482a
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8f31b7b2a19"
down_revision: Union[str, None] = "91d6c2fe482a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingestion_issues",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=True),
        sa.Column("touchpoint_reference", sa.String(length=128), nullable=True),
        sa.Column("observed_at_text", sa.String(length=128), nullable=True),
        sa.Column("issue_code", sa.String(length=64), nullable=False),
        sa.Column("detail", sa.String(length=512), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingestion_issues_event_id"), "ingestion_issues", ["event_id"], unique=False)
    op.create_index(op.f("ix_ingestion_issues_issue_code"), "ingestion_issues", ["issue_code"], unique=False)
    op.create_index(op.f("ix_ingestion_issues_received_at"), "ingestion_issues", ["received_at"], unique=False)
    op.create_index(op.f("ix_ingestion_issues_source_type"), "ingestion_issues", ["source_type"], unique=False)
    op.create_index(op.f("ix_ingestion_issues_touchpoint_reference"), "ingestion_issues", ["touchpoint_reference"], unique=False)

    op.create_table(
        "observation_revisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("observation_id", sa.String(length=36), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["observation_id"], ["observations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("observation_id", "revision_number", name="uq_observation_revision"),
    )
    op.create_index(op.f("ix_observation_revisions_observation_id"), "observation_revisions", ["observation_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_observation_revisions_observation_id"), table_name="observation_revisions")
    op.drop_table("observation_revisions")
    op.drop_index(op.f("ix_ingestion_issues_touchpoint_reference"), table_name="ingestion_issues")
    op.drop_index(op.f("ix_ingestion_issues_source_type"), table_name="ingestion_issues")
    op.drop_index(op.f("ix_ingestion_issues_received_at"), table_name="ingestion_issues")
    op.drop_index(op.f("ix_ingestion_issues_issue_code"), table_name="ingestion_issues")
    op.drop_index(op.f("ix_ingestion_issues_event_id"), table_name="ingestion_issues")
    op.drop_table("ingestion_issues")
