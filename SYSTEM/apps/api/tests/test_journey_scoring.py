from dataclasses import replace

import pytest

from app.journey_scoring import DEFAULT_EXPRESSION_VALUES, score_journey, summarize_journey_scores, validate_scoring_config
from app.sequence_analysis import SequenceAnalysisError, VisitSequence


def config(weights=(0.1, 0.2, 0.3, 0.4)):
    return {
        "expression_values": dict(DEFAULT_EXPRESSION_VALUES),
        "touchpoints": [{"id": str(i), "code": f"P{i}", "name": f"Point {i}", "sequence_order": i, "weight": weight}
                       for i, weight in enumerate(weights)],
    }


def sequence(states=("Neutral", "Happy", "Happy", "Sad"), points=(0, 1, 2, 3)):
    return VisitSequence("visit", states, tuple({"touchpoint_id": str(point), "observation_ids": [f"o{i}"]} for i, point in enumerate(points)))


def test_score_is_weighted_mean_of_values_and_invariant_to_weight_scale():
    result = score_journey(sequence(), config())
    assert result["score"] == pytest.approx(0.65)
    assert "coverage" not in result and "status" not in result
    assert sum(row["contribution"] for row in result["breakdown"]) == pytest.approx(result["score"])
    assert score_journey(sequence(), config((1, 2, 3, 4)))["score"] == pytest.approx(0.65)


def test_journey_uses_available_points_without_imputing_missing_labels():
    result = score_journey(sequence(("Neutral", "Happy"), (0, 2)), config())
    assert result["score"] == pytest.approx(0.875)
    assert result["breakdown"][1]["point_score"] is None
    assert summarize_journey_scores([result])["mean"] == pytest.approx(0.875)


def test_revisited_touchpoint_does_not_receive_its_weight_twice():
    result = score_journey(sequence(("Neutral", "Sad", "Happy"), (0, 3, 0)), config())
    assert result["breakdown"][0]["point_score"] == pytest.approx(0.75)
    assert result["score"] == pytest.approx(0.35)


def test_zero_weight_observed_point_does_not_produce_a_fake_zero_score():
    result = score_journey(sequence(("Happy",), (0,)), config((0, 1, 1, 1)))
    assert result["score"] is None
    assert summarize_journey_scores([result])["unscored_count"] == 1


def test_summary_averages_every_scored_journey():
    scores = [score_journey(sequence(), config()),
              score_journey(sequence(("Happy",), (0,)), config()),
              score_journey(sequence(("Happy",), (0,)), config((0, 1, 1, 1)))]
    summary = summarize_journey_scores(scores)
    assert summary == {"journey_count": 3, "unscored_count": 1, "mean": pytest.approx(0.825),
                       "minimum": pytest.approx(0.65), "maximum": 1.0}


@pytest.mark.parametrize("weights", [{}, {"p": 0}, {"p": -1}, {"p": float("nan")}, {"p": float("inf")}])
def test_invalid_weight_config_is_rejected(weights):
    with pytest.raises(SequenceAnalysisError):
        validate_scoring_config(DEFAULT_EXPRESSION_VALUES, weights)


def test_unknown_touchpoint_inconsistent_metadata_and_invalid_values_are_rejected():
    with pytest.raises(SequenceAnalysisError):
        score_journey(sequence(("Happy",), (99,)), config())
    with pytest.raises(SequenceAnalysisError):
        score_journey(replace(sequence(), metadata=()), config())
    for values in ({"Happy": 1}, {**DEFAULT_EXPRESSION_VALUES, "Happy": 2}):
        with pytest.raises(SequenceAnalysisError):
            validate_scoring_config(values, {"p": 1})
