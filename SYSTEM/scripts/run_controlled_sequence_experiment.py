from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sequenzo import SequenceData, get_distance_matrix
from sequenzo.clustering import cluster_labels_from_kmedoids_result, observation_silhouette
from sequenzo.clustering.k_medoids_range import k_medoids_range
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from demo_common import ARTIFACT_ROOT, login_client, save_json


STATES = ("Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral")
ARCHETYPES = {
    "archetype_01": ("Neutral", "Neutral", "Neutral", "Neutral"),
    "archetype_02": ("Happy", "Happy", "Happy", "Happy"),
    "archetype_03": ("Neutral", "Surprise", "Happy", "Happy"),
    "archetype_04": ("Neutral", "Sad", "Angry", "Angry"),
    # Cùng tỷ lệ trạng thái với archetype_03, chỉ khác thứ tự.
    "archetype_05": ("Happy", "Neutral", "Surprise", "Happy"),
}


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Không có dữ liệu để ghi: {path}")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def om_distance_matrix(visit_ids: list[str], sequences: list[tuple[str, ...]]) -> np.ndarray:
    columns = [f"state_{index + 1}" for index in range(max(map(len, sequences)))]
    frame = pd.DataFrame(
        [
            {"visit_id": visit_id, **dict(zip(columns, sequence, strict=True))}
            for visit_id, sequence in zip(visit_ids, sequences, strict=True)
        ]
    )
    with redirect_stdout(StringIO()):
        data = SequenceData(
            frame,
            time=columns,
            states=list(STATES),
            labels=list(STATES),
            id_col="visit_id",
        )
        result = get_distance_matrix(
            seqdata=data,
            method="OM",
            sm="CONSTANT",
            indel=1,
            norm="none",
            full_matrix=True,
        )
    return np.asarray(result, dtype=np.float64)


def baseline_distance_matrix(sequences: list[tuple[str, ...]]) -> np.ndarray:
    vectors = np.asarray(
        [[sequence.count(state) / len(sequence) for state in STATES] for sequence in sequences],
        dtype=np.float64,
    )
    differences = vectors[:, None, :] - vectors[None, :, :]
    return np.sqrt(np.sum(differences**2, axis=2))


def pam_select(
    matrix: np.ndarray,
    *,
    min_cluster_size_abs: int,
    min_cluster_ratio: float,
    asw_tolerance: float,
    random_state: int,
) -> dict:
    n_sequences = matrix.shape[0]
    n_min = max(min_cluster_size_abs, math.ceil(min_cluster_ratio * n_sequences))
    unique_profile_count = int(np.unique(matrix, axis=0).shape[0])
    k_max = min(n_sequences - 1, n_sequences // n_min, unique_profile_count)
    kvals = list(range(2, k_max + 1))
    with redirect_stdout(StringIO()):
        result = k_medoids_range(
            matrix,
            kvals,
            method="PAM",
            npass=1,
            n_boot=1,
            random_state=random_state,
        )
    candidates = []
    solutions: dict[int, dict] = {}
    for k in kvals:
        raw = np.asarray(result.clustering[f"cluster{k}"], dtype=np.int32)
        labels = cluster_labels_from_kmedoids_result(raw)
        sizes = np.bincount(labels, minlength=k)
        silhouettes = observation_silhouette(matrix, labels)
        asw = float(np.mean(silhouettes))
        accepted = bool(np.all(sizes >= n_min))
        candidates.append(
            {
                "k": k,
                "asw": asw,
                "min_cluster_size": int(sizes.min()),
                "max_cluster_size": int(sizes.max()),
                "required_min_cluster_size": n_min,
                "accepted": accepted,
            }
        )
        if accepted:
            solutions[k] = {"labels": labels, "silhouettes": silhouettes, "asw": asw}
    if not solutions:
        raise RuntimeError("Baseline không có phương án K hợp lệ")
    best_asw = max(item["asw"] for item in solutions.values())
    selected_k = min(k for k, item in solutions.items() if best_asw - item["asw"] <= asw_tolerance)
    return {"selected_k": selected_k, "candidate_metrics": candidates, **solutions[selected_k]}


def save_figures(output: Path, om_matrix: np.ndarray, labels: list[int], om_metrics: list[dict], baseline_metrics: list[dict]) -> None:
    accepted_om = [row for row in om_metrics if row["accepted"]]
    accepted_baseline = [row for row in baseline_metrics if row["accepted"]]
    fig, axis = plt.subplots(figsize=(8, 4.8))
    axis.plot([row["k"] for row in accepted_om], [row["asw"] for row in accepted_om], marker="o", label="Optimal Matching + PAM")
    axis.plot([row["k"] for row in accepted_baseline], [row["asw"] for row in accepted_baseline], marker="s", label="Tỷ lệ trạng thái + Euclidean + PAM")
    axis.set(xlabel="Số cụm K", ylabel="Average Silhouette Width", ylim=(-0.05, 1.05))
    axis.grid(alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(output / "asw_comparison.png", dpi=180)
    plt.close(fig)

    order = np.argsort(np.asarray(labels))
    fig, axis = plt.subplots(figsize=(7.4, 6.4))
    image = axis.imshow(om_matrix[np.ix_(order, order)], cmap="viridis", aspect="auto")
    axis.set(title="Ma trận khoảng cách Optimal Matching (sắp theo cụm)", xlabel="Chuỗi", ylabel="Chuỗi")
    fig.colorbar(image, ax=axis, label="Khoảng cách OM")
    fig.tight_layout()
    fig.savefig(output / "om_distance_heatmap.png", dpi=180)
    plt.close(fig)


def main(customer_count: int, seed: int, run_id: str) -> None:
    if customer_count < len(ARCHETYPES):
        raise SystemExit(f"Cần ít nhất {len(ARCHETYPES)} khách hàng")
    rng = random.Random(seed)
    start = datetime(2026, 10, 20, 9, 0, tzinfo=timezone(timedelta(hours=7)))
    output = ARTIFACT_ROOT / "experiment-runs" / run_id / "controlled-sequences"
    output.mkdir(parents=True, exist_ok=True)

    with login_client() as client:
        customer_page = client.get("/customers", params={"page_size": 100}).raise_for_status().json()
        candidates = sorted(
            [
                row
                for row in customer_page["items"]
                if row["status"] == "ACTIVE" and row["customer_code"].startswith(("CUS-KDEF-", "CUS-EXP-"))
            ],
            key=lambda row: row["customer_code"],
        )
        if len(candidates) < customer_count:
            raise SystemExit(f"Cần {customer_count} khách hàng demo, hiện có {len(candidates)}")
        customers = candidates[:customer_count]
        touchpoints = sorted(client.get("/touchpoints").raise_for_status().json(), key=lambda row: row["sequence_order"])
        if len(touchpoints) < 4:
            raise SystemExit("Cần ít nhất bốn điểm chạm")
        touchpoints = touchpoints[:4]

        observations: list[dict] = []
        planned_visits: list[dict] = []
        for customer_index, customer in enumerate(customers):
            for archetype_index, (archetype_id, sequence) in enumerate(ARCHETYPES.items()):
                visit_key = f"{run_id}-{customer['customer_code']}-{archetype_id}"
                visit_start = start + timedelta(days=archetype_index, minutes=customer_index * 20)
                event_ids = []
                for position, (touchpoint, label) in enumerate(zip(touchpoints, sequence, strict=True)):
                    event_id = f"{visit_key}-E{position + 1:02d}"
                    event_ids.append(event_id)
                    observations.append(
                        {
                            "event_id": event_id,
                            "simulation_run_id": run_id,
                            "touchpoint_id": touchpoint["id"],
                            "customer_id": customer["id"],
                            "observed_at": (visit_start + timedelta(minutes=position * 5)).isoformat(),
                            "expression_label": label,
                            "expression_confidence": round(rng.uniform(0.85, 0.99), 3),
                            "image_status": "VALID",
                            "expression_status": "VALID",
                            "identity_status": "MATCHED",
                        }
                    )
                planned_visits.append(
                    {
                        "visit_key": visit_key,
                        "customer_id": customer["id"],
                        "customer_code": customer["customer_code"],
                        "archetype_id": archetype_id,
                        "sequence": list(sequence),
                        "event_ids": event_ids,
                    }
                )

        response = client.post("/simulation/observations/batch", json={"observations": observations})
        response.raise_for_status()
        visits_by_event = {row["event_id"]: row["visit_id"] for row in response.json()["items"]}
        for row in planned_visits:
            actual_ids = {visits_by_event[event_id] for event_id in row["event_ids"]}
            if len(actual_ids) != 1 or None in actual_ids:
                raise RuntimeError(f"Các sự kiện không tạo đúng một visit: {row['visit_key']}")
            row["visit_id"] = next(iter(actual_ids))

        request = {
            "source_type": "SIMULATOR",
            "source_run_id": run_id,
            "min_states": 4,
            "min_cluster_size_abs": 5,
            "min_cluster_ratio": 0.05,
            "k_min": 2,
            "asw_tolerance": 0.02,
            "random_state": seed,
        }
        analysis_response = client.post("/sequence-analyses", json=request)
        analysis_response.raise_for_status()
        analysis = analysis_response.json()
        clusters = client.get(f"/sequence-analyses/{analysis['id']}/clusters").raise_for_status().json()
        assignments_page = client.get(
            f"/sequence-analyses/{analysis['id']}/assignments", params={"page_size": 200}
        ).raise_for_status().json()
        assignments = assignments_page["items"]

    truth_by_visit = {row["visit_id"]: row for row in planned_visits}
    assignments = sorted(assignments, key=lambda row: row["visit_id"])
    visit_ids = [row["visit_id"] for row in assignments]
    sequences = [tuple(row["sequence"]) for row in assignments]
    truth_labels = [truth_by_visit[visit_id]["archetype_id"] for visit_id in visit_ids]
    om_labels = [row["cluster_id"] for row in assignments]
    om_matrix = om_distance_matrix(visit_ids, sequences)
    matrix_checksum = hashlib.sha256(om_matrix.astype("<f8", copy=False).tobytes(order="C")).hexdigest()
    if matrix_checksum != analysis["distance_matrix_sha256"]:
        raise RuntimeError("Checksum ma trận OM tái tạo không khớp kết quả API")

    baseline_matrix = baseline_distance_matrix(sequences)
    baseline = pam_select(
        baseline_matrix,
        min_cluster_size_abs=5,
        min_cluster_ratio=0.05,
        asw_tolerance=0.02,
        random_state=seed,
    )
    baseline_labels = baseline["labels"].tolist()
    comparison = [
        {
            "method": "Optimal Matching + PAM",
            "selected_k": analysis["selected_k"],
            "asw": analysis["average_silhouette_width"],
            "ari": adjusted_rand_score(truth_labels, om_labels),
            "nmi": normalized_mutual_info_score(truth_labels, om_labels),
        },
        {
            "method": "State ratio + Euclidean + PAM",
            "selected_k": baseline["selected_k"],
            "asw": baseline["asw"],
            "ari": adjusted_rand_score(truth_labels, baseline_labels),
            "nmi": normalized_mutual_info_score(truth_labels, baseline_labels),
        },
    ]
    assignment_rows = [
        {
            "visit_id": visit_id,
            "customer_code": truth_by_visit[visit_id]["customer_code"],
            "archetype_id": truth_by_visit[visit_id]["archetype_id"],
            "sequence": " -> ".join(sequences[index]),
            "om_cluster_id": om_labels[index],
            "om_silhouette": assignments[index]["silhouette"],
            "om_distance_to_medoid": assignments[index]["distance_to_medoid"],
            "baseline_cluster_id": baseline_labels[index] + 1,
            "baseline_silhouette": float(baseline["silhouettes"][index]),
        }
        for index, visit_id in enumerate(visit_ids)
    ]

    np.save(output / "om_distance_matrix.npy", om_matrix)
    np.save(output / "baseline_distance_matrix.npy", baseline_matrix)
    write_rows(output / "assignments.csv", assignment_rows)
    write_rows(output / "method_comparison.csv", comparison)
    write_rows(output / "om_k_candidates.csv", analysis["candidate_metrics"])
    write_rows(output / "baseline_k_candidates.csv", baseline["candidate_metrics"])
    save_json(
        output / "manifest.json",
        {
            "simulation_run_id": run_id,
            "analysis_run_id": analysis["id"],
            "seed": seed,
            "customer_count": customer_count,
            "visit_count": len(planned_visits),
            "observation_count": len(observations),
            "archetypes": {key: list(value) for key, value in ARCHETYPES.items()},
            "visits": planned_visits,
        },
    )
    save_json(
        output / "results.json",
        {
            "analysis": analysis,
            "clusters": clusters,
            "comparison": comparison,
            "distance_matrix_sha256": matrix_checksum,
        },
    )
    save_figures(output, om_matrix, om_labels, analysis["candidate_metrics"], baseline["candidate_metrics"])
    print(json.dumps({"run_id": run_id, "analysis_run_id": analysis["id"], "comparison": comparison}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--customer-count", type=int, default=25)
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--run-id", default="SIM-CONTROLLED-20261008")
    args = parser.parse_args()
    main(args.customer_count, args.seed, args.run_id)
