from __future__ import annotations

import json
from datetime import datetime, timezone

from demo_common import ARTIFACT_ROOT, DATASET_ROOT, login_client, read_csv, save_json


def main() -> None:
    expected = json.loads((DATASET_ROOT / "expected" / "expected_visits.json").read_text(encoding="utf-8"))
    checks: list[dict] = []
    with login_client() as client:
        customers = {row["customer_code"]: row for row in client.get("/customers?page_size=100").raise_for_status().json()["items"]}
        touchpoints = {row["id"]: row["touchpoint_code"] for row in client.get("/touchpoints").raise_for_status().json()}
        visits = client.get("/visits").raise_for_status().json()
        for customer_code, rule in expected["customers"].items():
            customer = customers[customer_code]
            count = sum(visit["customer_id"] == customer["id"] for visit in visits)
            checks.append({"name": f"minimum visits for {customer_code}", "passed": count >= rule["minimum_visits"], "actual": count, "expected": rule["minimum_visits"]})
        event_scenarios = {row["event_id"]: row["scenario_id"] for row in read_csv("events.csv")}
        for visit in visits:
            detail = client.get(f"/visits/{visit['id']}").raise_for_status().json()
            scenario_ids = {event_scenarios.get(item["event_id"]) for item in detail["observations"]}
            for scenario_id in scenario_ids:
                if scenario_id not in expected["scenarios"]:
                    continue
                actual = [touchpoints[item["touchpoint_id"]] for item in detail["observations"] if event_scenarios.get(item["event_id"]) == scenario_id]
                wanted = expected["scenarios"][scenario_id]["touchpoints"]
                checks.append({"name": f"touchpoint sequence {scenario_id}", "passed": actual == wanted, "actual": actual, "expected": wanted})
        quality = client.get("/reports/data-quality").raise_for_status().json()
        distribution = client.get("/reports/expression-distribution").raise_for_status().json()
        changes = client.get("/reports/expression-changes").raise_for_status().json()
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "quality": quality,
    }
    output = ARTIFACT_ROOT / "demo-runs" / "latest"
    save_json(output / "verification.json", payload)
    save_json(output / "report_distribution.json", distribution)
    save_json(output / "report_changes.json", changes)
    print(f"Kết quả: {sum(check['passed'] for check in checks)}/{len(checks)} điều kiện đạt")
    if not payload["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

