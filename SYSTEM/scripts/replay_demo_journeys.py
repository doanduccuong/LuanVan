from __future__ import annotations

import argparse
import json
import time
from datetime import datetime

from demo_common import ARTIFACT_ROOT, DATASET_ROOT, login_client, read_csv


def main(scenario: str, speed: float, minimum_pass_rate: float) -> None:
    if not 0 <= minimum_pass_rate <= 1:
        raise SystemExit("minimum-pass-rate phải nằm trong [0, 1]")
    events = read_csv("events.csv")
    if scenario != "all":
        events = [row for row in events if row["scenario_id"] == scenario]
    events.sort(key=lambda row: (datetime.fromisoformat(row["observed_at"]), row["event_id"]))
    run_ids = {row.get("experiment_run_id", "") for row in events}
    if len(run_ids) != 1 or not next(iter(run_ids), ""):
        raise SystemExit("events.csv phải chứa đúng một experiment_run_id")
    experiment_run_id = next(iter(run_ids))
    with login_client() as client:
        customers = {row["id"]: row["customer_code"] for row in client.get("/customers?page_size=100").raise_for_status().json()["items"]}
        touchpoints = {row["touchpoint_code"]: row for row in client.get("/touchpoints").raise_for_status().json()}
        output_path = ARTIFACT_ROOT / "experiment-runs" / experiment_run_id / "replay_results.jsonl"
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
                        data={
                            "event_id": row["event_id"],
                            "touchpoint_id": touchpoints[row["touchpoint_code"]]["id"],
                            "observed_at": row["observed_at"],
                            "experiment_run_id": experiment_run_id,
                            "demo_data": "true",
                        },
                        files={"image": (image_path.name, handle, "image/jpeg")},
                    )
                payload = response.json()
                observations = payload.get("observations", [])
                actual_customers = [customers.get(item.get("customer_id")) for item in observations if item.get("customer_id")]
                actual_identity_statuses = [item.get("identity_status") for item in observations]
                actual_expression_labels = [item.get("expression_label") for item in observations]
                actual_visit_ids = [item.get("visit_id") for item in observations if item.get("visit_id")]
                expected_customer = row["expected_customer_code"] or None
                expected_identity = row["expected_identity_status"]
                expected_image = row["expected_image_status"]
                expected_face_count = int(row["expected_face_count"])
                image_ok = payload.get("image_status") == expected_image
                face_count_ok = payload.get("face_count") == expected_face_count
                if expected_customer:
                    # Chỉ quan sát đã ghép với khách hàng đăng ký được API lưu và trả về.
                    identity_ok = (
                        actual_customers.count(expected_customer) == 1
                        and actual_identity_statuses.count("MATCHED") == 1
                        and all(status == "MATCHED" for status in actual_identity_statuses)
                    )
                elif expected_identity == "NO_MATCH":
                    identity_ok = not observations
                else:
                    identity_ok = not observations
                record = {
                    "scenario_id": row["scenario_id"],
                    "experiment_run_id": experiment_run_id,
                    "archetype_id": row.get("archetype_id"),
                    "event_id": row["event_id"],
                    "source_subject_id": row["source_subject_id"],
                    "expected_image_status": expected_image,
                    "actual_image_status": payload.get("image_status"),
                    "expected_identity_status": expected_identity,
                    "actual_identity_statuses": actual_identity_statuses,
                    "expected_expression_label": row.get("expected_expression_label"),
                    "actual_expression_labels": actual_expression_labels,
                    "expected_customer_code": expected_customer,
                    "actual_customer_codes": actual_customers,
                    "actual_visit_ids": actual_visit_ids,
                    "expected_face_count": expected_face_count,
                    "face_count": payload.get("face_count"),
                    "http_status": response.status_code,
                    "passed": response.is_success and image_ok and face_count_ok and identity_ok,
                }
                total += 1
                passed += int(record["passed"])
                output.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
                print(row["event_id"], response.status_code, record["actual_image_status"], record["actual_identity_statuses"], record["passed"])
        summary = {
            "experiment_run_id": experiment_run_id,
            "total_capture_events": total,
            "passed_capture_events": passed,
            "failed_capture_events": total - passed,
        }
        (output_path.parent / "replay_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    pass_rate = passed / total if total else 0
    print(
        f"Kết quả phát lại ảnh: {passed}/{total} sự kiện đạt "
        f"({pass_rate:.1%}); ngưỡng yêu cầu {minimum_pass_rate:.1%}; lưu tại {output_path}"
    )
    if pass_rate < minimum_pass_rate:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="all")
    parser.add_argument("--speed", type=float, default=0)
    parser.add_argument(
        "--minimum-pass-rate",
        type=float,
        default=1,
        help="Tỷ lệ sự kiện phải khớp đầy đủ để lệnh trả mã 0; mọi lỗi vẫn được lưu vào artifact",
    )
    args = parser.parse_args()
    main(args.scenario, args.speed, args.minimum_pass_rate)
