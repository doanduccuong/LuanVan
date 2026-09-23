"""add simulation source and customer images

Revision ID: 91d6c2fe482a
Revises: 1c0a31f1078f
Create Date: 2026-09-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "91d6c2fe482a"
down_revision: Union[str, None] = "1c0a31f1078f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("profile_image_url", sa.String(length=512), nullable=True))
    op.add_column("observations", sa.Column("source_type", sa.String(length=32), nullable=False, server_default="CAMERA"))
    op.add_column("observations", sa.Column("simulation_run_id", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_observations_source_type"), "observations", ["source_type"], unique=False)
    op.create_index(op.f("ix_observations_simulation_run_id"), "observations", ["simulation_run_id"], unique=False)
    op.alter_column("observations", "source_type", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_observations_simulation_run_id"), table_name="observations")
    op.drop_index(op.f("ix_observations_source_type"), table_name="observations")
    op.drop_column("observations", "simulation_run_id")
    op.drop_column("observations", "source_type")
    op.drop_column("customers", "profile_image_url")
