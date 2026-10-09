from __future__ import annotations

import argparse
from datetime import datetime, timezone

from demo_common import ARTIFACT_ROOT, login_client, save_json


def main(
    *,
    source_type: str,
    source_run_id: str,
    min_states: int,
    min_cluster_size_abs: int,
    min_cluster_ratio: float,
    k_max: int | None,
    random_state: int,
) -> None:
    request = {
        "source_type": source_type,
        "source_run_id": source_run_id,
        "min_states": min_states,
        "min_cluster_size_abs": min_cluster_size_abs,
        "min_cluster_ratio": min_cluster_ratio,
        "k_max": k_max,
        "random_state": random_state,
    }
    with login_client() as client:
        response = client.post("/sequence-analyses", json=request)
        if response.is_error:
            raise SystemExit(f"Phân tích chuỗi thất bại ({response.status_code}): {response.text}")
        run = response.json()
        clusters = client.get(f"/sequence-analyses/{run['id']}/clusters").raise_for_status().json()
        assignments = client.get(
            f"/sequence-analyses/{run['id']}/assignments",
            params={"page_size": 200},
        ).raise_for_status().json()

    output = ARTIFACT_ROOT / "experiment-runs" / source_run_id / "sequence-analysis"
    save_json(
        output / "run.json",
        {"captured_at": datetime.now(timezone.utc).isoformat(), "request": request, "result": run},
    )
    save_json(output / "clusters.json", clusters)
    save_json(output / "assignments.json", assignments)
    print(
        f"Đã hoàn thành run {run['id']}: {run['used_visit_count']} chuỗi, "
        f"K={run['selected_k']}, ASW={run['average_silhouette_width']:.4f}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-type", choices=("CAMERA", "SIMULATOR"), required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--min-states", type=int, default=4)
    parser.add_argument("--min-cluster-size-abs", type=int, default=2)
    parser.add_argument("--min-cluster-ratio", type=float, default=0.05)
    parser.add_argument("--k-max", type=int)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()
    main(
        source_type=args.source_type,
        source_run_id=args.source_run_id,
        min_states=args.min_states,
        min_cluster_size_abs=args.min_cluster_size_abs,
        min_cluster_ratio=args.min_cluster_ratio,
        k_max=args.k_max,
        random_state=args.random_state,
    )
