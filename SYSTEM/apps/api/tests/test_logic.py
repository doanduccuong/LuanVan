from __future__ import annotations

from decimal import Decimal

import pytest

from app.logic import cosine_distance


def test_cosine_distance_identical_vectors():
    assert cosine_distance([1.0, 0.0], [1.0, 0.0]) == pytest.approx(0.0)


def test_cosine_distance_orthogonal_vectors():
    assert cosine_distance([1.0, 0.0], [0.0, 1.0]) == pytest.approx(1.0)


def test_cosine_distance_rejects_dimension_mismatch():
    with pytest.raises(ValueError):
        cosine_distance([1.0], [1.0, 0.0])

