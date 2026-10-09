from __future__ import annotations

import pytest

from emotion_finetuning.config import validate_training_config


def test_training_config_rejects_non_positive_learning_rate() -> None:
    config = {
        "training": {
            "batch_size": 32,
            "epochs": 2,
            "learning_rate": 0,
            "patience": 1,
            "min_delta": 0,
            "augmentation": {},
        }
    }
    with pytest.raises(ValueError, match="learning_rate"):
        validate_training_config(config)
