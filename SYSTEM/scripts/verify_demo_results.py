from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone

from demo_common import ARTIFACT_ROOT, DATASET_ROOT, login_client, read_csv, save_json


def main() -> None:
    expected = json.loads((DATASET_ROOT / "expected" / "expected_visits.json").read_text(encoding="utf-8"))
    experiment_run_id = expected["experiment_run_id"]
    event_rows = read_csv("events.csv")
    event_by_id = {row["event_id"]: row for row in event_rows}
    replay_path = ARTIFACT_ROOT / "experiment-runs" / experiment_run_id / "replay_results.jsonl"
    replay_rows = [
        json.loads(line)
        for line in replay_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    checks: list[dict] = []

    identity_correct = 0
    identity_no_match = 0
    identity_false_match = 0
    expression_pairs: list[tuple[str, str | None]] = []
    for row in replay_rows:
        actual_customers = row.get("actual_customer_codes") or []
        expected_customer = row["expected_customer_code"]
        if expected_customer in actual_customers:
            identity_correct += 1
        elif actual_customers:
            identity_false_match += 1
        else:
            identity_no_match += 1
        actual_expressions = row.get("actual_expression_labels") or []
        expression_pairs.append(
            (row["expected_expression_label"], actual_expressions[0] if actual_expressions else None)
        )

    expression_labels = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]
    confusion_matrix = {
        expected_label: {
            actual_label: sum(
                1
                for expected, actual in expression_pairs
                if expected == expected_label and actual == actual_label
            )
            for actual_label in expression_labels
        }
        for expected_label in expression_labels
    }
    per_class: dict[str, dict] = {}
    f1_values: list[float] = []
    for label in expression_labels:
        support = sum(1 for expected_label, _ in expression_pairs if expected_label == label)
        tp = sum(1 for expected_label, actual in expression_pairs if expected_label == actual == label)
        fp = sum(1 for expected_label, actual in expression_pairs if expected_label != label and actual == label)
        fn = sum(1 for expected_label, actual in expression_pairs if expected_label == label and actual != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        if support:
            f1_values.append(f1)
        per_class[label] = {
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    metrics = {
        "capture_event_count": len(replay_rows),
        "valid_image_count": sum(row.get("actual_image_status") == "VALID" for row in replay_rows),
        "identity": {
            "correct_match_count": identity_correct,
            "no_match_count": identity_no_match,
            "false_match_count": identity_false_match,
            "correct_match_rate": identity_correct / len(replay_rows),
        },
        "expression": {
            "accuracy": sum(expected == actual for expected, actual in expression_pairs) / len(expression_pairs),
            "macro_f1_present_classes": sum(f1_values) / len(f1_values),
            "expected_distribution": dict(Counter(expected for expected, _ in expression_pairs)),
            "predicted_distribution": dict(Counter(actual for _, actual in expression_pairs)),
            "per_class": per_class,
            "confusion_matrix": confusion_matrix,
        },
    }
    checks.extend(
        [
            {
                "name": "all KDEF camera frames processed as valid images",
                "passed": metrics["capture_event_count"] == expected["expected_event_count"]
                and metrics["valid_image_count"] == expected["expected_event_count"],
                "actual": metrics["valid_image_count"],
                "expected": expected["expected_event_count"],
            },
            {
                "name": "no cross-customer false match",
                "passed": identity_false_match == 0,
                "actual": identity_false_match,
                "expected": 0,
            },
        ]
    )

    with login_client() as client:
        customers = {
            row["customer_code"]: row
            for row in client.get("/customers?page_size=100").raise_for_status().json()["items"]
        }
        touchpoints = {
            row["id"]: row["touchpoint_code"]
            for row in client.get("/touchpoints").raise_for_status().json()
        }
        visits = client.get("/visits").raise_for_status().json()
        run_visits: list[dict] = []
        visits_by_customer: dict[str, list[dict]] = defaultdict(list)
        for visit in visits:
            detail = client.get(f"/visits/{visit['id']}").raise_for_status().json()
            observations = [
                item
                for item in detail["observations"]
                if item.get("experiment_run_id") == experiment_run_id
            ]
            if not observations:
                continue
            record = {"visit": visit, "observations": observations}
            run_visits.append(record)
            visits_by_customer[visit["customer_id"]].append(record)

        checks.append(
            {
                "name": "expected KDEF visit count",
                "passed": len(run_visits) == expected["expected_visit_count"],
                "actual": len(run_visits),
                "expected": expected["expected_visit_count"],
            }
        )
        for customer_code, rule in expected["customers"].items():
            customer = customers.get(customer_code)
            actual = len(visits_by_customer.get(customer["id"], [])) if customer else 0
            checks.append(
                {
                    "name": f"visit count {customer_code}",
                    "passed": actual == rule["expected_visits"],
                    "actual": actual,
                    "expected": rule["expected_visits"],
                }
            )

        complete_visit_count = 0
        for record in run_visits:
            observations = sorted(
                record["observations"],
                key=lambda item: (item["observed_at"], item["id"]),
            )
            event_metadata = [event_by_id[item["event_id"]] for item in observations]
            actual_touchpoints = [touchpoints[item["touchpoint_id"]] for item in observations]
            expected_touchpoints = [item["touchpoint_code"] for item in event_metadata]
            scenario_ids = {item["scenario_id"] for item in event_metadata}
            expected_full_order = ["TP-ENTRANCE", "TP-DISPLAY", "TP-CONSULT", "TP-CHECKOUT"]
            expected_positions = [expected_full_order.index(item) for item in actual_touchpoints]
            if len(observations) == expected["events_per_visit"]:
                complete_visit_count += 1
            checks.append(
                {
                    "name": f"observed touchpoints preserve chronology {record['visit']['id']}",
                    "passed": (
                        len(scenario_ids) == 1
                        and expected_positions == sorted(expected_positions)
                        and len(set(actual_touchpoints)) == len(actual_touchpoints)
                    ),
                    "actual": actual_touchpoints,
                    "expected": expected_touchpoints,
                }
            )

        analyses = client.get("/sequence-analyses", params={"source_type": "CAMERA"}).raise_for_status().json()
        matching = [
            item
            for item in analyses
            if item["source_run_id"] == experiment_run_id and item["status"] == "COMPLETED"
        ]
        checks.append(
            {
                "name": "completed sequence analysis",
                "passed": bool(matching),
                "actual": matching[0]["id"] if matching else None,
                "expected": "one completed analysis",
            }
        )
        if matching:
            checks.append(
                {
                    "name": "sequence analysis uses every complete four-touchpoint visit",
                    "passed": (
                        matching[0]["received_visit_count"] == expected["expected_visit_count"]
                        and matching[0]["used_visit_count"] == complete_visit_count
                        and matching[0]["excluded_visit_count"]
                        == expected["expected_visit_count"] - complete_visit_count
                    ),
                    "actual": {
                        "received": matching[0]["received_visit_count"],
                        "used": matching[0]["used_visit_count"],
                        "excluded": matching[0]["excluded_visit_count"],
                    },
                    "expected": {
                        "received": expected["expected_visit_count"],
                        "used": complete_visit_count,
                        "excluded": expected["expected_visit_count"] - complete_visit_count,
                    },
                }
            )
        quality = client.get("/reports/data-quality").raise_for_status().json()
        distribution = client.get("/reports/expression-distribution").raise_for_status().json()
        changes = client.get("/reports/expression-changes").raise_for_status().json()

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "experiment_run_id": experiment_run_id,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "metrics": metrics,
        "quality": quality,
    }
    output = ARTIFACT_ROOT / "experiment-runs" / experiment_run_id
    save_json(output / "verification.json", payload)
    save_json(output / "kdef_metrics.json", metrics)
    save_json(output / "report_distribution.json", distribution)
    save_json(output / "report_changes.json", changes)
    print(f"Kết quả: {sum(check['passed'] for check in checks)}/{len(checks)} điều kiện đạt")
    if not payload["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
