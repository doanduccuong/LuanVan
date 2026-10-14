"""Set and record the user-defined experimental journey scoring configuration."""
from __future__ import annotations

from demo_common import login_client


def main() -> None:
    with login_client() as client:
        current = client.get("/journey-scoring-settings").raise_for_status().json()
        points = current["touchpoints"]
        if len(points) != 4:
            raise SystemExit(f"Thực nghiệm cần đúng bốn điểm chạm, nhận {len(points)}")
        saved = client.put("/journey-scoring-settings", json={
            "revision": current["revision"],
            "expression_values": {
                "Angry": 0.1, "Disgust": 0.1, "Fear": 0.2, "Happy": 1.0,
                "Sad": 0.25, "Surprise": 0.5, "Neutral": 0.5,
            },
            "touchpoint_weights": {point["id"]: weight for point, weight in zip(points, (0.1, 0.2, 0.3, 0.4), strict=True)},
        }).raise_for_status().json()
    print(f"Đã lưu cấu hình điểm phiên bản {saved['revision']}: trọng số 0.10; 0.20; 0.30; 0.40")


if __name__ == "__main__":
    main()
