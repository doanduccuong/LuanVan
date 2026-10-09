"""add sequence analysis persistence and camera experiment run ids

Revision ID: f4c3d9a8b2e1
Revises: e7b4a91d2c60
Create Date: 2026-10-08 15:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f4c3d9a8b2e1"
down_revision: str | None = "e7b4a91d2c60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("capture_events", sa.Column("experiment_run_id", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_capture_events_experiment_run_id"), "capture_events", ["experiment_run_id"], unique=False)
    op.add_column("observations", sa.Column("experiment_run_id", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_observations_experiment_run_id"), "observations", ["experiment_run_id"], unique=False)

    op.create_table(
        "sequence_analysis_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_run_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("preprocessing_version", sa.String(length=64), nullable=False),
        sa.Column("algorithm_version", sa.String(length=128), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("candidate_metrics", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("received_visit_count", sa.Integer(), nullable=False),
        sa.Column("used_visit_count", sa.Integer(), nullable=False),
        sa.Column("excluded_visit_count", sa.Integer(), nullable=False),
        sa.Column("selected_k", sa.Integer(), nullable=True),
        sa.Column("average_silhouette_width", sa.Float(), nullable=True),
        sa.Column("distance_matrix_sha256", sa.String(length=64), nullable=True),
        sa.Column("error_detail", sa.String(length=1024), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sequence_analysis_runs_source_type"), "sequence_analysis_runs", ["source_type"], unique=False)
    op.create_index(op.f("ix_sequence_analysis_runs_source_run_id"), "sequence_analysis_runs", ["source_run_id"], unique=False)
    op.create_index(op.f("ix_sequence_analysis_runs_status"), "sequence_analysis_runs", ["status"], unique=False)

    op.create_table(
        "sequence_cluster_summaries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("medoid_visit_id", sa.String(length=36), nullable=False),
        sa.Column("medoid_sequence", sa.JSON(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("proportion", sa.Float(), nullable=False),
        sa.Column("mean_silhouette", sa.Float(), nullable=False),
        sa.Column("median_distance", sa.Float(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["medoid_visit_id"], ["visits.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["sequence_analysis_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "cluster_id", name="uq_sequence_cluster_run_cluster"),
    )
    op.create_index(op.f("ix_sequence_cluster_summaries_medoid_visit_id"), "sequence_cluster_summaries", ["medoid_visit_id"], unique=False)
    op.create_index(op.f("ix_sequence_cluster_summaries_run_id"), "sequence_cluster_summaries", ["run_id"], unique=False)

    op.create_table(
        "sequence_cluster_assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("visit_id", sa.String(length=36), nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.JSON(), nullable=False),
        sa.Column("sequence_metadata", sa.JSON(), nullable=False),
        sa.Column("distance_to_medoid", sa.Float(), nullable=False),
        sa.Column("silhouette", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["sequence_analysis_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "visit_id", name="uq_sequence_assignment_run_visit"),
    )
    op.create_index(op.f("ix_sequence_cluster_assignments_cluster_id"), "sequence_cluster_assignments", ["cluster_id"], unique=False)
    op.create_index(op.f("ix_sequence_cluster_assignments_run_id"), "sequence_cluster_assignments", ["run_id"], unique=False)
    op.create_index(op.f("ix_sequence_cluster_assignments_visit_id"), "sequence_cluster_assignments", ["visit_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sequence_cluster_assignments_visit_id"), table_name="sequence_cluster_assignments")
    op.drop_index(op.f("ix_sequence_cluster_assignments_run_id"), table_name="sequence_cluster_assignments")
    op.drop_index(op.f("ix_sequence_cluster_assignments_cluster_id"), table_name="sequence_cluster_assignments")
    op.drop_table("sequence_cluster_assignments")
    op.drop_index(op.f("ix_sequence_cluster_summaries_run_id"), table_name="sequence_cluster_summaries")
    op.drop_index(op.f("ix_sequence_cluster_summaries_medoid_visit_id"), table_name="sequence_cluster_summaries")
    op.drop_table("sequence_cluster_summaries")
    op.drop_index(op.f("ix_sequence_analysis_runs_status"), table_name="sequence_analysis_runs")
    op.drop_index(op.f("ix_sequence_analysis_runs_source_run_id"), table_name="sequence_analysis_runs")
    op.drop_index(op.f("ix_sequence_analysis_runs_source_type"), table_name="sequence_analysis_runs")
    op.drop_table("sequence_analysis_runs")
    op.drop_index(op.f("ix_observations_experiment_run_id"), table_name="observations")
    op.drop_column("observations", "experiment_run_id")
    op.drop_index(op.f("ix_capture_events_experiment_run_id"), table_name="capture_events")
    op.drop_column("capture_events", "experiment_run_id")
