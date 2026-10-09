from __future__ import annotations

import pytest

from expression_benchmark.config import ensure_private_test_allowed


def test_private_test_is_blocked_before_configuration_is_locked() -> None:
    with pytest.raises(PermissionError, match="PrivateTest"):
        ensure_private_test_allowed({"run": {"final_evaluation": False}})


def test_private_test_can_be_enabled_explicitly() -> None:
    ensure_private_test_allowed({"run": {"final_evaluation": True}})
