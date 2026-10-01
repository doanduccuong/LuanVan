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
        customers = {row["id"]: row["customer_code"] for row in client.get("/customers?page_size=100").raise_for_status().json()["items"]}
        touchpoints = {row["touchpoint_code"]: row for row in client.get("/touchpoints").raise_for_status().json()}
        output_path = ARTIFACT_ROOT / "experiment-runs" / "latest" / "replay_results.jsonl"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        previous_time = None
        passed = 0
        total = 0
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
                payload = response.json()
                observations = payload.get("observations", [])
                actual_customers = [customers.get(item.get("customer_id")) for item in observations if item.get("customer_id")]
                actual_identity_statuses = [item.get("identity_status") for item in observations]
                expected_customer = row["expected_customer_code"] or None
                expected_identity = row["expected_identity_status"]
                expected_image = row["expected_image_status"]
                expected_face_count = int(row["expected_face_count"])
                image_ok = payload.get("image_status") == expected_image
                face_count_ok = payload.get("face_count") == expected_face_count
                if expected_customer:
                    identity_ok = expected_customer in actual_customers and "MATCHED" in actual_identity_statuses
                elif expected_identity == "NO_MATCH":
                    identity_ok = bool(actual_identity_statuses) and all(status == "NO_MATCH" for status in actual_identity_statuses)
                else:
                    identity_ok = not observations
                record = {
                    "scenario_id": row["scenario_id"],
                    "event_id": row["event_id"],
                    "source_subject_id": row["source_subject_id"],
                    "expected_image_status": expected_image,
                    "actual_image_status": payload.get("image_status"),
                    "expected_identity_status": expected_identity,
                    "actual_identity_statuses": actual_identity_statuses,
                    "expected_customer_code": expected_customer,
                    "actual_customer_codes": actual_customers,
                    "expected_face_count": expected_face_count,
                    "face_count": payload.get("face_count"),
                    "http_status": response.status_code,
                    "passed": response.is_success and image_ok and face_count_ok and identity_ok,
                }
                total += 1
                passed += int(record["passed"])
                output.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
                print(row["event_id"], response.status_code, record["actual_image_status"], record["actual_identity_statuses"], record["passed"])
        summary = {"total_capture_events": total, "passed_capture_events": passed, "failed_capture_events": total - passed}
        (output_path.parent / "replay_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Kết quả phát lại ảnh: {passed}/{total} sự kiện đạt; lưu tại {output_path}")
    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="all")
    parser.add_argument("--speed", type=float, default=0)
    args = parser.parse_args()
    main(args.scenario, args.speed)
