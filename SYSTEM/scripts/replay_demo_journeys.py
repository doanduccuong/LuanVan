from __future__ import annotations

import argparse
import json
import time
from datetime import datetime

from demo_common import ARTIFACT_ROOT, DATASET_ROOT, login_client, read_csv


def main(scenario: str, speed: float) -> None:
    events = read_csv("events.csv")
    if scenario != "all":
        events = [row for row in events if row["scenario_id"] == scenario]
    with login_client() as client:
        touchpoints = {row["touchpoint_code"]: row for row in client.get("/touchpoints").raise_for_status().json()}
        output_path = ARTIFACT_ROOT / "demo-runs" / "latest" / "replay_results.jsonl"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        previous_time = None
        with output_path.open("w", encoding="utf-8") as output:
            for row in events:
                observed_at = datetime.fromisoformat(row["observed_at"])
                if speed > 0 and previous_time:
                    time.sleep(max(0, (observed_at - previous_time).total_seconds() / speed))
                previous_time = observed_at
                image_path = DATASET_ROOT / row["image_path"]
                with image_path.open("rb") as handle:
                    response = client.post(
                        "/observations",
                        data={"event_id": row["event_id"], "touchpoint_id": touchpoints[row["touchpoint_code"]]["id"], "observed_at": row["observed_at"], "demo_data": "true"},
                        files={"image": (image_path.name, handle, "image/jpeg")},
                    )
                record = {"scenario_id": row["scenario_id"], "event_id": row["event_id"], "http_status": response.status_code, "response": response.json()}
                output.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
                print(row["event_id"], response.status_code, record["response"].get("image_status"))
    print(f"Đã lưu kết quả tại {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="all")
    parser.add_argument("--speed", type=float, default=0)
    args = parser.parse_args()
    main(args.scenario, args.speed)

