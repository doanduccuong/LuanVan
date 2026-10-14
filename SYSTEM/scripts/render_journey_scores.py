"""Render and independently audit scores exported from an actual API run."""
from __future__ import annotations

import json
import math
import os
import shutil
from pathlib import Path
from statistics import mean, median

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = os.environ["SOURCE_RUN_ID"]
RUN_ROOT = ROOT / "artifacts" / "experiment-runs" / RUN_ID


def main() -> None:
    analysis = json.loads((RUN_ROOT / "journey-scoring/run.json").read_text())["result"]
    scores = json.loads((RUN_ROOT / "journey-scoring/scores.json").read_text())["items"]
    config = analysis["scoring_config"]
    checks = 0
    for row in scores:
        assert "coverage" not in row and "status" not in row
        present = [point for point in row["breakdown"] if point["states"]]
        denominator = sum(point["weight"] for point in present)
        expected = sum(point["weight"] * mean(config["expression_values"][label] for label in point["states"]) for point in present) / denominator if denominator else None
        if expected is None:
            assert row["score"] is None
        else:
            assert 0 <= row["score"] <= 1
            assert math.isclose(expected, row["score"], abs_tol=1e-12)
            assert math.isclose(sum(point["contribution"] for point in row["breakdown"]), expected, abs_tol=1e-12)
        checks += 1
    scored = [row for row in scores if row["score"] is not None]
    assert "complete_count" not in analysis["scoring_summary"]
    assert "partial_count" not in analysis["scoring_summary"]
    if scored:
        assert math.isclose(analysis["scoring_summary"]["mean"], mean(row["score"] for row in scored), abs_tol=1e-12)
    ordered = sorted(scored, key=lambda row: (row["score"], row["visit_id"]))
    examples = [ordered[0], ordered[len(ordered)//2], ordered[-1]] if ordered else []
    summary = {**analysis["scoring_summary"], "median": median(row["score"] for row in scored) if scored else None,
               "examples": examples, "verified_journeys": checks,
               "scoring_run_id": analysis["id"], "source_run_id": RUN_ID, "scoring_config": config}
    (RUN_ROOT / "journey_scoring_metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    chart_dir = RUN_ROOT / "charts"
    chart_dir.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(8.5, 4.3))
    ax.hist([row["score"] for row in scored], bins=np.linspace(0, 1, 11), color="#0f766e", edgecolor="white")
    ax.set(xlim=(0, 1), xlabel="Điểm tổng hợp hành trình", ylabel="Số hành trình", title=f"Phân bố điểm của {len(scored)} hành trình")
    ax.grid(axis="y", alpha=0.15)
    fig.tight_layout()
    output = chart_dir / "journey_scores.png"
    fig.savefig(output, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    if os.environ.get("UPDATE_REPORT", "false").lower() == "true":
        shutil.copy2(output, ROOT.parent / "BAO CAO/Hinhve/Chuong5/5_31_phan_bo_diem_hanh_trinh.png")
    print(f"Đã kiểm tra độc lập {checks} điểm hành trình và xuất biểu đồ: {output}")


if __name__ == "__main__":
    main()
