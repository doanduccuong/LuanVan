"""Configurable weighted journey scores, independent of classifier confidence."""
from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean

from .sequence_analysis import EXPRESSION_STATES, SequenceAnalysisError, VisitSequence


SCORING_VERSION = "weighted-touchpoint-mean-v1"
# These are editable experimental conventions, not published normative ratings.
DEFAULT_EXPRESSION_VALUES = {
    "Angry": 0.10, "Disgust": 0.10, "Fear": 0.20, "Happy": 1.00,
    "Sad": 0.25, "Surprise": 0.50, "Neutral": 0.50,
}


def validate_scoring_config(values: dict[str, float], weights: dict[str, float]) -> None:
    if set(values) != set(EXPRESSION_STATES):
        raise SequenceAnalysisError("Bảng điểm phải có đủ và chỉ gồm bảy nhãn biểu cảm")
    if any(not math.isfinite(value) or not 0 <= value <= 1 for value in values.values()):
        raise SequenceAnalysisError("Điểm biểu cảm phải là số hữu hạn trong [0, 1]")
    if not weights or any(not math.isfinite(value) or value < 0 for value in weights.values()):
        raise SequenceAnalysisError("Trọng số điểm chạm phải là số hữu hạn không âm")
    if not math.isfinite(sum(weights.values())) or sum(weights.values()) <= 0:
        raise SequenceAnalysisError("Tổng trọng số điểm chạm phải lớn hơn 0")


def score_journey(sequence: VisitSequence, config: dict) -> dict:
    values = config["expression_values"]
    touchpoints = config["touchpoints"]
    weights = {item["id"]: float(item["weight"]) for item in touchpoints}
    validate_scoring_config(values, weights)
    if len(sequence.states) != len(sequence.metadata):
        raise SequenceAnalysisError("Chuỗi và thông tin điểm chạm không cùng kích thước")
    point_states: dict[str, list[str]] = defaultdict(list)
    point_observations: dict[str, list[str]] = defaultdict(list)
    for state, metadata in zip(sequence.states, sequence.metadata, strict=True):
        point_id = metadata["touchpoint_id"]
        if point_id not in weights:
            raise SequenceAnalysisError(f"Điểm chạm {point_id} chưa có trong cấu hình tính điểm")
        if state not in values:
            raise SequenceAnalysisError(f"Biểu cảm {state} chưa có điểm quy đổi")
        point_states[point_id].append(state)
        point_observations[point_id].extend(metadata.get("observation_ids", []))
    observed_weight = sum(weights[key] for key in point_states)
    breakdown = []
    for point in touchpoints:
        states = point_states.get(point["id"], [])
        point_score = mean(values[state] for state in states) if states else None
        normalized_weight = point["weight"] / observed_weight if states and observed_weight > 0 else 0.0
        breakdown.append({
            "touchpoint_id": point["id"], "touchpoint_name": point["name"],
            "touchpoint_code": point["code"], "sequence_order": point["sequence_order"],
            "states": states, "state_values": [values[state] for state in states],
            "point_score": point_score, "weight": point["weight"],
            "normalized_weight": normalized_weight,
            "contribution": normalized_weight * point_score if point_score is not None else 0.0,
            "observation_ids": point_observations.get(point["id"], []),
        })
    return {
        "visit_id": sequence.visit_id, "sequence": list(sequence.states),
        "sequence_metadata": list(sequence.metadata),
        "score": sum(item["contribution"] for item in breakdown) if observed_weight > 0 else None,
        "breakdown": breakdown,
    }


def summarize_journey_scores(scores: list[dict]) -> dict:
    values = [item["score"] for item in scores if item["score"] is not None]
    return {
        "journey_count": len(scores),
        "unscored_count": sum(item["score"] is None for item in scores),
        "mean": mean(values) if values else None,
        "minimum": min(values) if values else None,
        "maximum": max(values) if values else None,
    }
