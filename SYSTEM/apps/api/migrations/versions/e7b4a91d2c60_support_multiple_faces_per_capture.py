"""support multiple faces per capture

Revision ID: e7b4a91d2c60
Revises: c8f31b7b2a19
Create Date: 2026-10-01 11:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e7b4a91d2c60"
down_revision: str | None = "c8f31b7b2a19"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "capture_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("touchpoint_id", sa.String(length=36), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("image_status", sa.String(length=32), nullable=False),
        sa.Column("face_count", sa.Integer(), nullable=False),
        sa.Column("detector_version", sa.String(length=255), nullable=True),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("simulation_run_id", sa.String(length=64), nullable=True),
        sa.Column("demo_data", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["touchpoint_id"], ["touchpoints.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_capture_events_demo_data"), "capture_events", ["demo_data"], unique=False)
    op.create_index(op.f("ix_capture_events_event_id"), "capture_events", ["event_id"], unique=True)
    op.create_index(op.f("ix_capture_events_image_status"), "capture_events", ["image_status"], unique=False)
    op.create_index(op.f("ix_capture_events_observed_at"), "capture_events", ["observed_at"], unique=False)
    op.create_index(op.f("ix_capture_events_simulation_run_id"), "capture_events", ["simulation_run_id"], unique=False)
    op.create_index(op.f("ix_capture_events_source_type"), "capture_events", ["source_type"], unique=False)
    op.create_index(op.f("ix_capture_events_touchpoint_id"), "capture_events", ["touchpoint_id"], unique=False)

    op.add_column("observations", sa.Column("capture_event_id", sa.String(length=36), nullable=True))
    op.add_column("observations", sa.Column("face_index", sa.Integer(), nullable=True))
    op.add_column("observations", sa.Column("bounding_box", sa.JSON(), nullable=True))
    op.add_column("observations", sa.Column("detection_score", sa.Float(), nullable=True))

    op.execute(
        """
        INSERT INTO capture_events (
            id, event_id, touchpoint_id, observed_at, received_at, image_status,
            face_count, detector_version, source_type, simulation_run_id, demo_data, created_at
        )
        SELECT
            id, event_id, touchpoint_id, observed_at, received_at, image_status,
            CASE WHEN image_status = 'VALID' THEN 1 ELSE 0 END,
            detector_version, source_type, simulation_run_id, demo_data, created_at
        FROM observations
        """
    )
    op.execute("UPDATE observations SET capture_event_id = id, face_index = 0")
    with op.batch_alter_table("observations") as batch_op:
        batch_op.alter_column("capture_event_id", existing_type=sa.String(length=36), nullable=False)
        batch_op.alter_column("face_index", existing_type=sa.Integer(), nullable=False)
        batch_op.create_foreign_key(
            "fk_observations_capture_event_id",
            "capture_events",
            ["capture_event_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index(op.f("ix_observations_capture_event_id"), ["capture_event_id"], unique=False)
        batch_op.drop_index(op.f("ix_observations_event_id"))
        batch_op.create_index(op.f("ix_observations_event_id"), ["event_id"], unique=False)
        batch_op.create_unique_constraint("uq_observation_event_face", ["event_id", "face_index"])


def downgrade() -> None:
    raise RuntimeError(
        "Không thể tự động hạ cấp vì một khung hình có thể chứa nhiều quan sát; "
        "cần xuất và hợp nhất dữ liệu trước khi quay lại lược đồ một quan sát cho mỗi sự kiện."
    )
