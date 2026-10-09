from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
RUN_ID = "KDEF-KAGGLE-20261008-LIVE"
RUN_ROOT = ROOT / "artifacts" / "experiment-runs" / RUN_ID
CHART_ROOT = RUN_ROOT / "charts"
REPORT_ROOT = PROJECT_ROOT / "BAO CAO" / "Hinhve" / "Chuong5"


def save_chart(figure: plt.Figure, artifact_name: str, report_name: str) -> None:
    CHART_ROOT.mkdir(parents=True, exist_ok=True)
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact_path = CHART_ROOT / artifact_name
    figure.savefig(artifact_path, dpi=200, bbox_inches="tight", facecolor="white")
    shutil.copy2(artifact_path, REPORT_ROOT / report_name)
    plt.close(figure)


def render_confusion_matrix(metrics: dict) -> None:
    expression = metrics["expression"]
    expected_labels = [
        label
        for label in ("Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral")
        if expression["per_class"][label]["support"] > 0
    ]
    predicted_labels = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]
    counts = np.array(
        [
            [expression["confusion_matrix"][expected][predicted] for predicted in predicted_labels]
            for expected in expected_labels
        ],
        dtype=int,
    )
    row_totals = counts.sum(axis=1, keepdims=True)
    proportions = np.divide(
        counts,
        row_totals,
        out=np.zeros_like(counts, dtype=float),
        where=row_totals != 0,
    )

    fig, ax = plt.subplots(figsize=(9.2, 6.2))
    image = ax.imshow(proportions, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    for row in range(counts.shape[0]):
        for column in range(counts.shape[1]):
            value = proportions[row, column]
            color = "white" if value >= 0.55 else "#111827"
            ax.text(
                column,
                row,
                f"{counts[row, column]}\n({value * 100:.0f}%)",
                ha="center",
                va="center",
                fontsize=8.5,
                color=color,
            )
    ax.set_xticks(range(len(predicted_labels)), predicted_labels, rotation=30, ha="right")
    ax.set_yticks(range(len(expected_labels)), expected_labels)
    ax.set_xlabel("Nhãn do DeepFace dự đoán")
    ax.set_ylabel("Nhãn thư mục KDEF dùng làm đối chiếu")
    ax.set_title("Ma trận nhầm lẫn biểu cảm trên 100 khung camera KDEF")
    colorbar = fig.colorbar(image, ax=ax, fraction=0.04, pad=0.03)
    colorbar.set_label("Tỷ lệ theo từng nhãn đối chiếu")
    fig.text(
        0.01,
        0.01,
        f"Run {RUN_ID}; ô hiển thị số mẫu và tỷ lệ theo hàng. Accuracy = {expression['accuracy']:.3f}; "
        f"Macro-F1 (5 lớp có mẫu) = {expression['macro_f1_present_classes']:.3f}.",
        fontsize=8.5,
        color="#374151",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save_chart(fig, "expression_confusion_matrix.png", "5_20_kdef_ma_tran_nham_lan.png")


def render_identity_outcomes(metrics: dict) -> None:
    identity = metrics["identity"]
    labels = ["Ghép đúng khách", "Không khớp", "Ghép nhầm khách"]
    values = [
        identity["correct_match_count"],
        identity["no_match_count"],
        identity["false_match_count"],
    ]
    colors = ["#0f766e", "#f59e0b", "#dc2626"]
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    bars = ax.bar(labels, values, color=colors, width=0.62)
    ax.set_ylim(0, 105)
    ax.set_ylabel("Số khung camera")
    ax.set_title("Kết quả ghép định danh trên 100 khung camera KDEF")
    ax.grid(axis="y", alpha=0.22)
    for bar, value in zip(bars, values, strict=True):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 2, str(value), ha="center", fontweight="bold")
    fig.text(
        0.01,
        0.01,
        f"Run {RUN_ID}; 100/100 ảnh hợp lệ; ngưỡng ArcFace được hiệu chỉnh trên 35 ảnh dành riêng.",
        fontsize=8.5,
        color="#374151",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save_chart(fig, "identity_outcomes.png", "5_21_kdef_ket_qua_dinh_danh.png")


def render_k_selection(run_payload: dict) -> None:
    result = run_payload["result"]
    candidates = result["candidate_metrics"]
    fig, ax = plt.subplots(figsize=(9.2, 5.5))
    ks = [item["k"] for item in candidates]
    asws = [item["asw"] for item in candidates]
    ax.plot(ks, asws, color="#64748b", linewidth=1.5, zorder=1)
    for item in candidates:
        selected = item["k"] == result["selected_k"]
        color = "#0f766e" if item["accepted"] else "#cbd5e1"
        marker = "*" if selected else "o"
        size = 180 if selected else 72
        ax.scatter(item["k"], item["asw"], s=size, marker=marker, color=color, edgecolor="#334155", zorder=2)
        if selected:
            ax.annotate(
                f"Chọn K={item['k']}\nASW={item['asw']:.3f}",
                (item["k"], item["asw"]),
                xytext=(0, 18),
                textcoords="offset points",
                ha="center",
                fontsize=9,
            )
    ax.set_xticks(ks)
    ax.set_ylim(0, 0.6)
    ax.set_xlabel("Số cụm K")
    ax.set_ylabel("Average Silhouette Width")
    ax.set_title("Lựa chọn số cụm trên 22 chuỗi hợp lệ từ camera KDEF")
    ax.grid(axis="y", alpha=0.22)
    ax.text(
        0.99,
        0.03,
        "Điểm xanh: phương án đạt kích thước cụm tối thiểu\nĐiểm xám: bị loại vì có cụm chỉ 1 chuỗi",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8.5,
        color="#475569",
    )
    fig.text(
        0.01,
        0.01,
        f"Run {RUN_ID}; 25 lượt nhận vào, 22 lượt đủ 4 trạng thái, 3 lượt bị loại.",
        fontsize=8.5,
        color="#374151",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save_chart(fig, "k_selection.png", "5_26_kdef_chon_so_cum.png")


def main() -> None:
    metrics = json.loads((RUN_ROOT / "kdef_metrics.json").read_text(encoding="utf-8"))
    run_payload = json.loads((RUN_ROOT / "sequence-analysis" / "run.json").read_text(encoding="utf-8"))
    if metrics["capture_event_count"] != 100:
        raise RuntimeError("Artifact KDEF không có đúng 100 khung camera")
    if run_payload["result"]["source_run_id"] != RUN_ID:
        raise RuntimeError("Run phân cụm không thuộc artifact KDEF đang vẽ")
    render_confusion_matrix(metrics)
    render_identity_outcomes(metrics)
    render_k_selection(run_payload)
    print(f"Đã tạo biểu đồ từ artifact thật tại {CHART_ROOT}")


if __name__ == "__main__":
    main()
