from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

import app.sequence_analysis as sequence_analysis
from app.sequence_analysis import (
    AnalysisConfig,
    SequenceObservation,
    VisitSequence,
    cluster_visit_sequences,
    prepare_visit_sequences,
)


def observation(
    observation_id: str,
    visit_id: str,
    touchpoint_id: str,
    minute: int,
    label: str,
    confidence: float = 0.9,
) -> SequenceObservation:
    return SequenceObservation(
        observation_id=observation_id,
        visit_id=visit_id,
        touchpoint_id=touchpoint_id,
        touchpoint_name=touchpoint_id,
        observed_at=datetime(2026, 10, 8, 9, minute, tzinfo=timezone.utc),
        expression_label=label,
        expression_confidence=confidence,
    )


def test_prepare_sequences_keeps_equal_states_at_different_touchpoints():
    prepared = prepare_visit_sequences(
        [
            observation("o1", "v1", "entrance", 0, "Neutral"),
            observation("o2", "v1", "display", 5, "Neutral"),
            observation("o3", "v1", "consult", 10, "Happy"),
            observation("o4", "v1", "checkout", 15, "Happy"),
        ],
        min_states=3,
    )
    assert prepared.received_visit_count == 1
    assert prepared.excluded == []
    assert prepared.sequences[0].states == ("Neutral", "Neutral", "Happy", "Happy")
    assert [item["touchpoint_id"] for item in prepared.sequences[0].metadata] == [
        "entrance",
        "display",
        "consult",
        "checkout",
    ]


def test_prepare_sequences_condenses_repeated_frames_inside_one_touchpoint():
    prepared = prepare_visit_sequences(
        [
            observation("o1", "v1", "entrance", 0, "Neutral", 0.8),
            observation("o2", "v1", "entrance", 1, "Happy", 0.2),
            observation("o3", "v1", "entrance", 2, "Neutral", 0.7),
            observation("o4", "v1", "display", 5, "Happy"),
            observation("o5", "v1", "checkout", 10, "Happy"),
        ],
        min_states=3,
    )
    assert prepared.sequences[0].states == ("Neutral", "Happy", "Happy")
    assert prepared.sequences[0].metadata[0]["support_count"] == 3


def test_om_and_pam_recover_two_clear_sequence_groups():
    sequences = [
        VisitSequence(f"positive-{index}", ("Neutral", "Happy", "Happy", "Happy"), ())
        for index in range(4)
    ] + [
        VisitSequence(f"negative-{index}", ("Sad", "Sad", "Angry", "Angry"), ())
        for index in range(4)
    ]
    result = cluster_visit_sequences(
        sequences,
        AnalysisConfig(min_states=4, min_cluster_size_abs=2, min_cluster_ratio=0.1, k_max=2),
    )
    assert result.selected_k == 2
    assert result.average_silhouette_width == pytest.approx(1.0)
    assert sorted(cluster["size"] for cluster in result.clusters) == [4, 4]
    assert {tuple(cluster["medoid_sequence"]) for cluster in result.clusters} == {
        ("Neutral", "Happy", "Happy", "Happy"),
        ("Sad", "Sad", "Angry", "Angry"),
    }


def test_k_range_is_capped_by_number_of_distinct_sequences():
    archetypes = [
        ("Neutral", "Neutral", "Neutral", "Neutral"),
        ("Happy", "Happy", "Happy", "Happy"),
        ("Neutral", "Surprise", "Happy", "Happy"),
        ("Neutral", "Sad", "Angry", "Angry"),
        ("Happy", "Neutral", "Surprise", "Happy"),
    ]
    sequences = [
        VisitSequence(f"type-{kind}-{repeat}", states, ())
        for kind, states in enumerate(archetypes)
        for repeat in range(5)
    ]
    result = cluster_visit_sequences(
        sequences,
        AnalysisConfig(min_states=4, min_cluster_size_abs=2, min_cluster_ratio=0.05),
    )
    assert result.selected_k == 5
    assert max(item["k"] for item in result.candidate_metrics) == 5
    assert any("chuỗi trạng thái phân biệt" in warning for warning in result.warnings)


def test_undefined_silhouette_is_recorded_as_zero(monkeypatch):
    sequences = [
        VisitSequence(f"positive-{index}", ("Neutral", "Happy", "Happy", "Happy"), ())
        for index in range(2)
    ] + [
        VisitSequence(f"negative-{index}", ("Sad", "Sad", "Angry", "Angry"), ())
        for index in range(2)
    ]

    monkeypatch.setattr(
        sequence_analysis,
        "observation_silhouette",
        lambda _matrix, _labels: np.array([1.0, np.nan, 1.0, np.nan]),
    )
    result = cluster_visit_sequences(
        sequences,
        AnalysisConfig(min_states=4, min_cluster_size_abs=2, min_cluster_ratio=0.1, k_max=2),
    )

    assert result.average_silhouette_width == pytest.approx(0.5)
    assert result.candidate_metrics[0]["undefined_silhouette_count"] == 2
    assert any("quy ước bằng 0" in warning for warning in result.warnings)
