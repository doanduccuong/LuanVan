"""Persist configurable journey scoring and immutable per-run results."""
from alembic import op
import sqlalchemy as sa

revision = "a3b8e02d6c41"
down_revision = "f4c3d9a8b2e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "journey_scoring_settings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("expression_values", sa.JSON(), nullable=False),
        sa.Column("touchpoint_weights", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "journey_scoring_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_run_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("scoring_config", sa.JSON(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_journey_scoring_runs_source_type", "journey_scoring_runs", ["source_type"])
    op.create_index("ix_journey_scoring_runs_source_run_id", "journey_scoring_runs", ["source_run_id"])
    op.create_table(
        "sequence_journey_scores",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("journey_scoring_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("visit_id", sa.String(36), sa.ForeignKey("visits.id"), nullable=False),
        sa.Column("sequence", sa.JSON(), nullable=False),
        sa.Column("sequence_metadata", sa.JSON(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("coverage", sa.Float(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("breakdown", sa.JSON(), nullable=False),
        sa.UniqueConstraint("run_id", "visit_id", name="uq_journey_score_run_visit"),
    )
    op.create_index("ix_sequence_journey_scores_run_id", "sequence_journey_scores", ["run_id"])
    op.create_index("ix_sequence_journey_scores_visit_id", "sequence_journey_scores", ["visit_id"])


def downgrade() -> None:
    op.drop_table("sequence_journey_scores")
    op.drop_table("journey_scoring_runs")
    op.drop_table("journey_scoring_settings")
