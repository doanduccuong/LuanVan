from __future__ import annotations

LABELS = (
    "Angry",
    "Disgust",
    "Fear",
    "Happy",
    "Sad",
    "Surprise",
    "Neutral",
)

SPLITS = ("Training", "PublicTest", "PrivateTest")
EXPECTED_COUNTS = {"Training": 28_709, "PublicTest": 3_589, "PrivateTest": 3_589}
IMAGE_HEIGHT = 48
IMAGE_WIDTH = 48
PIXEL_COUNT = IMAGE_HEIGHT * IMAGE_WIDTH
