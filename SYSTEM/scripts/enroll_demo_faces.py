from __future__ import annotations

import argparse

from demo_common import DATASET_ROOT, login_client, read_csv


def main(limit: int | None = None) -> None:
    with login_client() as client:
        customers = {row["customer_code"]: row for row in client.get("/customers?page_size=100").raise_for_status().json()["items"]}
        rows = read_csv("customers.csv")
        if limit is not None:
            rows = rows[:limit]
        for row in rows:
            customer = customers[row["customer_code"]]
            client.put(f"/customers/{customer['id']}/face-consent", json={"consent": True}).raise_for_status()
            existing = client.get(f"/customers/{customer['id']}/face-templates").raise_for_status().json()
            if existing:
                print(f"Bỏ qua {row['customer_code']}: đã có {len(existing)} mẫu khuôn mặt")
                continue
            for image_path in sorted((DATASET_ROOT / "enrollment" / row["subject_id"]).glob("*.jpg")):
                with image_path.open("rb") as handle:
                    response = client.post(f"/customers/{customer['id']}/face-templates", files={"image": (image_path.name, handle, "image/jpeg")})
                response.raise_for_status()
                print(f"Đã đăng ký {row['customer_code']}: {image_path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    main(args.limit)
