from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np


def _pattern(label: int, variant: int) -> np.ndarray:
    image = np.zeros((48, 48), dtype=np.uint8)
    row = 4 + label * 6
    image[max(0, row - 1) : min(48, row + 2), :] = 180 + (variant % 3) * 20
    column = 5 + label * 5
    image[:, max(0, column - 1) : min(48, column + 2)] = 80 + (variant % 4) * 10
    rng = np.random.default_rng(label * 10_000 + variant)
    noise = rng.integers(0, 12, size=(48, 48), dtype=np.uint8)
    return np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tạo dữ liệu nhỏ chỉ để kiểm tra kỹ thuật đường ống.")
    parser.add_argument("output", type=Path)
    parser.add_argument("--training-per-class", type=int, default=4)
    parser.add_argument("--evaluation-per-class", type=int, default=2)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["emotion", "pixels", "Usage"])
        for split, count in (
            ("Training", args.training_per_class),
            ("PublicTest", args.evaluation_per_class),
            ("PrivateTest", args.evaluation_per_class),
        ):
            split_offset = {"Training": 0, "PublicTest": 100, "PrivateTest": 200}[split]
            for label in range(7):
                for variant in range(count):
                    image = _pattern(label, split_offset + variant)
                    writer.writerow([label, " ".join(map(str, image.ravel())), split])
    print(f"Đã tạo dữ liệu smoke test: {args.output}")


if __name__ == "__main__":
    main()
