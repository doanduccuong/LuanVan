"""Run weighted scoring for every journey, independently of clustering."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from demo_common import ARTIFACT_ROOT, login_client, save_json


def main(source_type: str, source_run_id: str) -> None:
    with login_client() as client:
        run = client.post("/journey-scoring-runs", json={"source_type": source_type, "source_run_id": source_run_id}).raise_for_status().json()
        scores = []
        page = 1
        while True:
            payload = client.get(f"/journey-scoring-runs/{run['id']}/scores", params={"page": page, "page_size": 200}).raise_for_status().json()
            scores.extend(payload["items"])
            if len(scores) >= payload["total"]:
                break
            page += 1
    output = ARTIFACT_ROOT / "experiment-runs" / source_run_id / "journey-scoring"
    save_json(output / "run.json", {"captured_at": datetime.now(timezone.utc).isoformat(), "result": run})
    save_json(output / "scores.json", {"items": scores, "total": len(scores)})
    print(f"Đã tính điểm {len(scores)} hành trình: {run['id']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-type", choices=("CAMERA", "SIMULATOR"), required=True)
    parser.add_argument("--source-run-id", required=True)
    args = parser.parse_args()
    main(args.source_type, args.source_run_id)
