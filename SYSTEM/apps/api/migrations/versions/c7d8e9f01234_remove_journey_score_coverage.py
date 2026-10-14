"""Keep journey scores without the derived coverage metric and its labels."""
from statistics import mean

from alembic import op
import sqlalchemy as sa

revision = "c7d8e9f01234"
down_revision = "b5c6f941e320"
branch_labels = None
depends_on = None


def _refresh_summaries(bind, *, legacy: bool = False) -> None:
    runs = sa.table("journey_scoring_runs", sa.column("id", sa.String()), sa.column("summary", sa.JSON()))
    columns = [sa.column("run_id", sa.String()), sa.column("score", sa.Float())]
    if legacy:
        columns.append(sa.column("status", sa.String()))
    scores = sa.table("sequence_journey_scores", *columns)
    for run_id in bind.scalars(sa.select(runs.c.id)).all():
        rows = bind.execute(sa.select(scores).where(scores.c.run_id == run_id)).mappings().all()
        values = [row["score"] for row in rows if row["score"] is not None
                  and (not legacy or row["status"] == "COMPLETE")]
        summary = {"journey_count": len(rows), "unscored_count": sum(row["score"] is None for row in rows),
                   "mean": mean(values) if values else None,
                   "minimum": min(values) if values else None, "maximum": max(values) if values else None}
        if legacy:
            summary.update(complete_count=sum(row["status"] == "COMPLETE" for row in rows),
                           partial_count=sum(row["status"] == "PARTIAL" for row in rows))
        bind.execute(runs.update().where(runs.c.id == run_id).values(summary=summary))


def upgrade() -> None:
    op.drop_column("sequence_journey_scores", "coverage")
    op.drop_column("sequence_journey_scores", "status")
    _refresh_summaries(op.get_bind())


def downgrade() -> None:
    op.add_column("sequence_journey_scores", sa.Column("coverage", sa.Float(), nullable=True))
    op.add_column("sequence_journey_scores", sa.Column("status", sa.String(32), nullable=True))
    bind = op.get_bind()
    runs = sa.table("journey_scoring_runs", sa.column("id", sa.String()), sa.column("scoring_config", sa.JSON()))
    scores = sa.table("sequence_journey_scores", sa.column("id", sa.String()), sa.column("run_id", sa.String()),
                      sa.column("breakdown", sa.JSON()), sa.column("coverage", sa.Float()), sa.column("status", sa.String()))
    rows = bind.execute(sa.select(scores.c.id, scores.c.breakdown, runs.c.scoring_config)
                        .select_from(scores.join(runs, scores.c.run_id == runs.c.id))).mappings().all()
    for row in rows:
        weights = {point["id"]: point["weight"] for point in row["scoring_config"]["touchpoints"]}
        observed = sum(weights[point["touchpoint_id"]] for point in row["breakdown"] if point["states"])
        coverage = observed / sum(weights.values())
        status = "NO_WEIGHT" if observed <= 0 else ("COMPLETE" if abs(coverage - 1) < 1e-9 else "PARTIAL")
        bind.execute(scores.update().where(scores.c.id == row["id"]).values(coverage=coverage, status=status))
    op.alter_column("sequence_journey_scores", "coverage", nullable=False)
    op.alter_column("sequence_journey_scores", "status", nullable=False)
    _refresh_summaries(bind, legacy=True)
