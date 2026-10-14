"""Check persisted sequences against raw responses and source manifests."""
import json
from collections import Counter

from demo_common import ARTIFACT_ROOT, DATASET_ROOT, save_json


def main():
    manifest = json.loads((DATASET_ROOT / "kdef_demo_manifest.json").read_text())
    expected = json.loads(
        (DATASET_ROOT / "expected" / "expected_visits.json").read_text(encoding="utf-8")
    )
    root = ARTIFACT_ROOT / "experiment-runs" / manifest["experiment_run_id"]
    rows = [json.loads(line) for line in (root / "replay_results.jsonl").read_text().splitlines()]
    visits = json.loads((root / "visits.json").read_text())
    assignments = json.loads((root / "sequence-analysis/assignments.json").read_text())
    clusters = json.loads((root / "sequence-analysis/clusters.json").read_text())
    run = json.loads((root / "sequence-analysis/run.json").read_text())["result"]
    by_visit = {item["visit"]["id"]: item["observations"] for item in visits}
    raw = {obs["id"]: obs for row in rows for obs in row["response"]["observations"]}
    assert (
        len(rows)
        == len({row["event_id"] for row in rows})
        == expected["expected_event_count"]
    )
    assert all(row["http_status"] == 201 and row["face_count"] == 1 for row in rows)
    assert len(raw) == sum(len(obs) for obs in by_visit.values())
    assert assignments["total"] == len(assignments["items"]) == run["used_visit_count"]
    assert sum(cluster["size"] for cluster in clusters) == run["used_visit_count"]
    for assignment in assignments["items"]:
        observations = sorted(by_visit[assignment["visit_id"]], key=lambda obs: (obs["observed_at"], obs["id"]))
        assert assignment["sequence"] == [obs["expression_label"] for obs in observations]
        assert [meta["observation_ids"] for meta in assignment["sequence_metadata"]] == [[obs["id"]] for obs in observations]
        for obs in observations:
            assert obs["expression_label"] == raw[obs["id"]]["expression_label"]
            assert obs["source_type"] == "CAMERA"
            assert obs["experiment_run_id"] == manifest["experiment_run_id"]
    sizes = Counter(item["cluster_id"] for item in assignments["items"])
    for cluster in clusters:
        assert cluster["size"] == sizes[cluster["cluster_id"]]
        medoid = next(item for item in assignments["items"] if item["visit_id"] == cluster["medoid_visit_id"])
        assert medoid["cluster_id"] == cluster["cluster_id"]
        assert medoid["sequence"] == cluster["medoid_sequence"]
    excluded = {item["visit_id"] for item in run["parameters"]["excluded_visits"]}
    assert excluded == {visit_id for visit_id, obs in by_visit.items() if len(obs) < 4}
    metrics = json.loads((root / "kdef_metrics.json").read_text())
    assert sum(sum(row.values()) for row in metrics["expression"]["confusion_matrix"].values()) == len(rows)
    failures = [row for row in rows if not row["passed"]]
    save_json(root / "failed-events.json", failures)
    save_json(root / "trace-audit.json", {
        "passed": True, "capture_events": len(rows), "stored_observations": len(raw),
        "verified_assignments": len(assignments["items"]), "verified_medoids": len(clusters),
        "excluded_visits": len(excluded), "failed_events": len(failures),
        "checks": ["raw API labels equal stored observations and clustering sequences",
                   "all sequence metadata observation IDs resolve to raw API responses",
                   "cluster sizes and medoids agree with assignments",
                   "missing-state visits equal excluded visits", "confusion counts include missing results"],
    })
    print("Raw response / observation / sequence / medoid trace audit passed.")


if __name__ == "__main__":
    main()
