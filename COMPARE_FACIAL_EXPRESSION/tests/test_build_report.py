from __future__ import annotations

import json
from pathlib import Path

import pytest

from expression_benchmark.build_report import build_comparison


def test_report_refuses_smoke_results(tmp_path: Path) -> None:
    (tmp_path / "run_manifest.json").write_text(
        json.dumps({"smoke_test": True, "final_evaluation": True}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="smoke"):
        build_comparison(tmp_path)
