from __future__ import annotations

import numpy as np

from expression_benchmark.adapters.lbp_svm import LBPSVMAdapter, extract_spatial_lbp


def test_spatial_lbp_has_fixed_shape() -> None:
    images = np.zeros((2, 48, 48), dtype=np.uint8)
    features = extract_spatial_lbp(images, grid_rows=6, grid_cols=6)
    assert features.shape == (2, 360)
    np.testing.assert_allclose(features.reshape(2, 36, 10).sum(axis=2), 1.0)


def test_lbp_svm_returns_seven_scores() -> None:
    rng = np.random.default_rng(42)
    images = rng.integers(0, 256, size=(21, 48, 48), dtype=np.uint8)
    labels = np.repeat(np.arange(7), 3)
    adapter = LBPSVMAdapter(seed=42)
    adapter.fit(images, labels)
    result = adapter.predict(images[:4])
    result.validate(4)
