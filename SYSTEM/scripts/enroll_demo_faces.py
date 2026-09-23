from __future__ import annotations

from demo_common import DATASET_ROOT, login_client, read_csv


def main() -> None:
    with login_client() as client:
        customers = {row["customer_code"]: row for row in client.get("/customers?page_size=100").raise_for_status().json()["items"]}
        for row in read_csv("customers.csv"):
            customer = customers[row["customer_code"]]
            client.put(f"/customers/{customer['id']}/face-consent", json={"consent": True}).raise_for_status()
            for image_path in sorted((DATASET_ROOT / "enrollment" / row["subject_id"]).glob("*.jpg")):
                with image_path.open("rb") as handle:
                    response = client.post(f"/customers/{customer['id']}/face-templates", files={"image": (image_path.name, handle, "image/jpeg")})
                response.raise_for_status()
                print(f"Đã đăng ký {row['customer_code']}: {image_path.name}")


if __name__ == "__main__":
    main()

