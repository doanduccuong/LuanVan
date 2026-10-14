"""Align early scoring installations with independent scoring runs."""
from alembic import op
import sqlalchemy as sa

revision = "b5c6f941e320"
down_revision = "a3b8e02d6c41"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    foreign_keys = inspector.get_foreign_keys("sequence_journey_scores")
    for constraint in foreign_keys:
        if constraint["constrained_columns"] == ["run_id"] and constraint["referred_table"] != "journey_scoring_runs":
            count = bind.scalar(sa.text("SELECT count(*) FROM sequence_journey_scores"))
            if count:
                raise RuntimeError("Cần chuyển dữ liệu điểm cũ sang lần tính điểm độc lập trước khi nâng cấp")
            op.drop_constraint(constraint["name"], "sequence_journey_scores", type_="foreignkey")
            op.create_foreign_key("fk_journey_score_run", "sequence_journey_scores", "journey_scoring_runs", ["run_id"], ["id"], ondelete="CASCADE")
    if "excluded_from_clustering" in {column["name"] for column in inspector.get_columns("sequence_journey_scores")}:
        op.drop_column("sequence_journey_scores", "excluded_from_clustering")


def downgrade() -> None:
    pass
