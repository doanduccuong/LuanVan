"""Validate generated inputs before any inference, without selecting by model outcomes."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime

from demo_common import ARTIFACT_ROOT, DATASET_ROOT, read_csv, save_json


def main():
    manifest = json.loads((DATASET_ROOT / "kdef_demo_manifest.json").read_text())
    expected = json.loads(
        (DATASET_ROOT / "expected" / "expected_visits.json").read_text(encoding="utf-8")
    )
    with (DATASET_ROOT / "image_manifest.csv").open() as handle:
        images = list(csv.DictReader(handle))
    roles = defaultdict(set)
    for image in images:
        roles[image["role"]].add(image["source_sha256"])
        assert hashlib.sha256((DATASET_ROOT / image["output"]).read_bytes()).hexdigest() == image["output_sha256"]
    assert not roles["enrollment"] & roles["calibration"]
    assert not roles["observation"] & (roles["enrollment"] | roles["calibration"])
    events = read_csv("events.csv")
    expected_event_count = expected["expected_event_count"]
    expected_visit_count = expected["expected_visit_count"]
    assert len(events) == len({event["event_id"] for event in events}) == expected_event_count
    visits = defaultdict(list)
    for event in events:
        assert event["experiment_run_id"] == manifest["experiment_run_id"]
        assert "archetype_id" not in event
        visits[event["scenario_id"]].append(event)
    order = ["TP-ENTRANCE", "TP-DISPLAY", "TP-CONSULT", "TP-CHECKOUT"]
    for visit in visits.values():
        visit.sort(key=lambda row: datetime.fromisoformat(row["observed_at"]))
        assert [row["touchpoint_code"] for row in visit] == order
        times = [datetime.fromisoformat(row["observed_at"]) for row in visit]
        gaps = [(later - earlier).total_seconds() / 60 for earlier, later in zip(times, times[1:])]
        assert all(5 <= gap <= 15 for gap in gaps)
    assert len(visits) == expected_visit_count
    all_gaps = []
    for visit in visits.values():
        times = [datetime.fromisoformat(row["observed_at"]) for row in visit]
        all_gaps.extend((later - earlier).total_seconds() / 60 for earlier, later in zip(times, times[1:]))
    assert len(set(all_gaps)) > 1
    output = ARTIFACT_ROOT / "experiment-runs" / manifest["experiment_run_id"]
    save_json(output / "input-audit.json", {
        "passed": True, "source_roles_disjoint_by_sha256": True,
        "events": len(events), "planned_visits": len(visits),
        "unique_sources_by_role": {role: len(paths) for role, paths in roles.items()},
        "label_counts": dict(Counter(row["expected_expression_label"] for row in events)),
        "touchpoint_gap_minutes": dict(Counter(str(int(gap)) for gap in all_gaps)),
        "camera_seed": manifest["camera_seed"],
    })
    print(
        f"Input audit passed: {expected_event_count} frames, "
        f"{expected_visit_count} planned visits; reserved source hashes excluded."
    )


if __name__ == "__main__":
    main()
