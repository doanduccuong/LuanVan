from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import PercentFormatter

from app.threshold_calibration import build_roc_curve, roc_auc, select_roc_threshold


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vẽ đường cong ROC hiệu chỉnh ngưỡng đối sánh ArcFace."
    )
    parser.add_argument(
        "--distances",
        type=Path,
        required=True,
        help="Tệp calibration-distances.json chứa khoảng cách cùng người và khác người.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Đường dẫn ảnh PNG đầu ra.",
    )
    parser.add_argument(
        "--target-fpr",
        type=float,
        default=0.10,
        help="FPR mục tiêu dùng để chọn điểm vận hành (mặc định: 0.10).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = json.loads(args.distances.read_text(encoding="utf-8"))
    positive_distances = data["positive_distances"]
    negative_distances = data["negative_distances"]

    points = build_roc_curve(positive_distances, negative_distances)
    selected = select_roc_threshold(
        points, target_false_positive_rate=args.target_fpr
    )
    area = roc_auc(points)

    false_positive_rates = [point.false_positive_rate for point in points]
    true_positive_rates = [point.true_positive_rate for point in points]
    zoom_x_max = max(0.005, min(0.20, args.target_fpr * 1.20))
    zoom_y_min = max(0.0, min(0.90, selected.true_positive_rate - 0.08))

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
        }
    )
    figure, (axis_full, axis_zoom) = plt.subplots(
        1,
        2,
        figsize=(10.0, 4.25),
        gridspec_kw={"width_ratios": [1.05, 1]},
        constrained_layout=True,
    )

    axis_full.step(
        false_positive_rates,
        true_positive_rates,
        where="post",
        color="#1769AA",
        linewidth=2.2,
        label="Đường ROC",
    )
    axis_full.plot(
        [0, 1],
        [0, 1],
        color="#7A8492",
        linewidth=1.2,
        linestyle="--",
        label="Phân loại ngẫu nhiên",
    )
    axis_full.scatter(
        [selected.false_positive_rate],
        [selected.true_positive_rate],
        color="#B03A2E",
        edgecolor="white",
        linewidth=0.9,
        s=58,
        zorder=5,
    )
    axis_full.add_patch(
        Rectangle(
            (0.0, zoom_y_min),
            zoom_x_max,
            1.0 - zoom_y_min,
            fill=False,
            edgecolor="#B03A2E",
            linewidth=1.1,
            linestyle=":",
        )
    )
    axis_full.text(
        0.97,
        0.08,
        f"AUC = {area:.4f}".replace(".", ","),
        transform=axis_full.transAxes,
        ha="right",
        va="bottom",
        fontsize=10,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "white",
            "edgecolor": "#AAB2BD",
            "alpha": 0.95,
        },
    )

    axis_zoom.step(
        false_positive_rates,
        true_positive_rates,
        where="post",
        color="#1769AA",
        linewidth=2.2,
    )
    axis_zoom.scatter(
        [selected.false_positive_rate],
        [selected.true_positive_rate],
        color="#B03A2E",
        edgecolor="white",
        linewidth=0.9,
        s=64,
        zorder=5,
    )
    annotation = (
        f"Ngưỡng = {selected.threshold:.4f}\n"
        f"TPR = {selected.true_positive_rate * 100:.2f}%\n"
        f"FPR = {selected.false_positive_rate * 100:.0f}%"
    ).replace(".", ",")
    axis_zoom.annotate(
        annotation,
        xy=(selected.false_positive_rate, selected.true_positive_rate),
        xytext=(zoom_x_max * 0.33, zoom_y_min + 0.025),
        textcoords="data",
        arrowprops={"arrowstyle": "->", "color": "#B03A2E", "linewidth": 1.1},
        bbox={
            "boxstyle": "round,pad=0.30",
            "facecolor": "white",
            "edgecolor": "#B03A2E",
            "alpha": 0.96,
        },
    )

    axis_full.set_title("(a) Toàn bộ đường cong ROC")
    axis_full.set_xlabel("Tỷ lệ dương tính giả (FPR)")
    axis_full.set_ylabel("Tỷ lệ dương tính thật (TPR)")
    axis_full.set_xlim(-0.02, 1.0)
    axis_full.set_ylim(0.0, 1.02)
    axis_full.set_xticks([value / 10 for value in range(0, 11, 2)])
    axis_full.set_yticks([value / 10 for value in range(0, 11, 2)])
    axis_full.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    axis_full.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    axis_full.legend(loc="center right", frameon=False, fontsize=9)

    axis_zoom.set_title("(b) Phóng đại quanh điểm vận hành")
    axis_zoom.set_xlabel("Tỷ lệ dương tính giả (FPR)")
    axis_zoom.set_xlim(-zoom_x_max * 0.04, zoom_x_max)
    axis_zoom.set_ylim(zoom_y_min, 1.005)
    axis_zoom.set_xticks([zoom_x_max * index / 6 for index in range(7)])
    axis_zoom.set_yticks(
        [value / 100 for value in range(int(zoom_y_min * 100 / 5) * 5, 101, 5)]
    )
    axis_zoom.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    axis_zoom.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))

    for axis in (axis_full, axis_zoom):
        axis.grid(True, color="#D9DEE5", linewidth=0.65, alpha=0.75)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(direction="out", length=3.5, width=0.8)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, dpi=300, facecolor="white")
    plt.close(figure)

    print(f"Đã tạo {args.output}")
    print(
        f"AUC={area:.6f}; threshold={selected.threshold:.6f}; "
        f"TPR={selected.true_positive_rate:.6f}; FPR={selected.false_positive_rate:.6f}"
    )


if __name__ == "__main__":
    main()
