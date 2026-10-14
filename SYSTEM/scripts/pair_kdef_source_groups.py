from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np

from demo_common import save_json


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Ghép 140 mã nhóm KDEF đã ẩn danh thành 70 cặp phiên bằng "
            "tâm embedding ArcFace và điều kiện láng giềng gần nhất hai chiều."
        )
    )
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--holdout-group",
        action="append",
        default=[],
        help=(
            "Mã nhóm dùng trong thực nghiệm đầu cuối; toàn bộ cặp phiên chứa mã "
            "này bị loại khỏi tập hiệu chỉnh. Có thể lặp tùy chọn."
        ),
    )
    parser.add_argument(
        "--calibration-identity-count",
        type=int,
        default=35,
        help="Số người dùng để hiệu chỉnh, mặc định 35.",
    )
    parser.add_argument(
        "--selection-seed",
        type=int,
        default=20261008,
        help="Seed chọn người hiệu chỉnh và một phiên đại diện của mỗi người.",
    )
    args = parser.parse_args()

    payload = json.loads(args.embeddings.read_text(encoding="utf-8"))
    grouped: dict[str, list[np.ndarray]] = {}
    for relative_path, row in payload["images"].items():
        parts = Path(relative_path).parts
        if len(parts) < 3 or parts[0] != "calibration":
            raise ValueError(f"Đường dẫn cache không hợp lệ: {relative_path}")
        grouped.setdefault(parts[1], []).append(
            np.asarray(row["embedding"], dtype=np.float64)
        )

    if len(grouped) != 140 or any(len(vectors) != 7 for vectors in grouped.values()):
        raise ValueError("Cần đúng 140 mã nhóm, mỗi mã có 7 embedding")

    centroids: dict[str, np.ndarray] = {}
    for group_id, vectors in grouped.items():
        centroid = np.mean(vectors, axis=0)
        centroids[group_id] = centroid / np.linalg.norm(centroid)

    distances: dict[tuple[str, str], float] = {}
    nearest: dict[str, tuple[float, str]] = {}
    for group_a, centroid_a in centroids.items():
        candidates: list[tuple[float, str]] = []
        for group_b, centroid_b in centroids.items():
            if group_a == group_b:
                continue
            pair = tuple(sorted((group_a, group_b)))
            distance = distances.setdefault(
                pair,
                1.0 - float(np.dot(centroid_a, centroid_b)),
            )
            candidates.append((distance, group_b))
        nearest[group_a] = min(candidates)

    pairs: list[dict[str, float | str]] = []
    covered: set[str] = set()
    for group_a in sorted(centroids):
        distance, group_b = nearest[group_a]
        if group_a >= group_b or nearest[group_b][1] != group_a:
            continue
        pairs.append(
            {
                "group_a": group_a,
                "group_b": group_b,
                "centroid_cosine_distance": distance,
            }
        )
        covered.update((group_a, group_b))

    if len(pairs) != 70 or len(covered) != 140:
        raise ValueError(
            f"Không thu được 70 cặp rời nhau: pairs={len(pairs)}, covered={len(covered)}"
        )

    paired_keys = {
        tuple(sorted((str(row["group_a"]), str(row["group_b"]))))
        for row in pairs
    }
    non_pair_distances = [
        distance
        for pair, distance in distances.items()
        if pair not in paired_keys
    ]
    holdout_groups = set(args.holdout_group)
    unknown_holdouts = sorted(holdout_groups - set(grouped))
    if unknown_holdouts:
        raise ValueError(f"Mã holdout không tồn tại: {unknown_holdouts}")
    holdout_pairs = [
        row
        for row in pairs
        if str(row["group_a"]) in holdout_groups
        or str(row["group_b"]) in holdout_groups
    ]
    if len(holdout_pairs) != len(holdout_groups):
        raise ValueError(
            "Các mã holdout phải thuộc những cặp người khác nhau: "
            f"groups={len(holdout_groups)}, pairs={len(holdout_pairs)}"
        )

    candidate_pairs = [row for row in pairs if row not in holdout_pairs]
    calibration_identity_count = args.calibration_identity_count
    if not 1 <= calibration_identity_count <= len(candidate_pairs):
        raise ValueError(
            "Số người hiệu chỉnh phải nằm trong [1, "
            f"{len(candidate_pairs)}] khi đã giữ lại {len(holdout_pairs)} người"
        )

    rng = random.Random(args.selection_seed)
    selected_pairs = rng.sample(candidate_pairs, calibration_identity_count)
    selected_pair_keys = {
        tuple(sorted((str(row["group_a"]), str(row["group_b"]))))
        for row in selected_pairs
    }
    selected_groups = []
    for row in selected_pairs:
        representatives = (str(row["group_a"]), str(row["group_b"]))
        selected_groups.append(rng.choice(representatives))
    selected_groups.sort()
    reserved_pairs = [
        row
        for row in pairs
        if tuple(sorted((str(row["group_a"]), str(row["group_b"]))))
        not in selected_pair_keys
    ]
    reserved_groups = []
    for row in reserved_pairs:
        representatives = (str(row["group_a"]), str(row["group_b"]))
        explicit_holdout = [group for group in representatives if group in holdout_groups]
        reserved_groups.append(explicit_holdout[0] if explicit_holdout else representatives[0])
    reserved_groups.sort()
    result = {
        "method": "mutual-nearest ArcFace centroid pairing",
        "source_group_count": len(grouped),
        "pair_count": len(pairs),
        "images_per_group": 7,
        "pairs": pairs,
        "calibration_identity_count": calibration_identity_count,
        "remaining_identity_count": len(pairs) - calibration_identity_count,
        "selection_seed": args.selection_seed,
        "selected_identity_pairs": selected_pairs,
        "selected_groups": selected_groups,
        "holdout_groups": sorted(holdout_groups),
        "holdout_identity_pairs": holdout_pairs,
        "reserved_identity_pairs": reserved_pairs,
        "reserved_groups": reserved_groups,
        "validation": {
            "maximum_paired_centroid_distance": max(
                float(row["centroid_cosine_distance"]) for row in pairs
            ),
            "minimum_non_paired_centroid_distance": min(non_pair_distances),
            "all_pairs_are_mutual_nearest": True,
            "all_groups_are_covered_once": True,
            "holdout_identities_excluded_from_calibration": not any(
                row in selected_pairs for row in holdout_pairs
            ),
        },
        "limitation": (
            "Pair labels are reconstructed from ArcFace embeddings because the processed "
            "mirror does not preserve original KDEF subject and session identifiers."
        ),
    }
    save_json(args.output.expanduser().resolve(), result)
    print(
        f"Đã ghép {len(grouped)} mã thành {len(pairs)} người; "
        f"chọn {len(selected_groups)} người hiệu chỉnh, "
        f"giữ lại {len(reserved_pairs)} người; "
        f"max_pair={result['validation']['maximum_paired_centroid_distance']:.6f}; "
        f"min_non_pair={result['validation']['minimum_non_paired_centroid_distance']:.6f}"
    )


if __name__ == "__main__":
    main()
