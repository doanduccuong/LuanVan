from __future__ import annotations

from collections import defaultdict

from demo_common import login_client, read_csv


def main() -> None:
    with login_client() as client:
        existing_customers = {row["customer_code"]: row for row in client.get("/customers?page_size=100").raise_for_status().json()["items"]}
        for row in read_csv("customers.csv"):
            if row["customer_code"] in existing_customers:
                continue
            response = client.post("/customers", json={"customer_code": row["customer_code"], "full_name": row["full_name"], "phone": row["phone"], "email": row["email"], "face_consent": True, "demo_data": True})
            response.raise_for_status()

        existing_categories = {row["category_code"]: row for row in client.get("/product-categories").raise_for_status().json()}
        for row in read_csv("product_categories.csv"):
            if row["category_code"] not in existing_categories:
                response = client.post("/product-categories", json={**row, "demo_data": True})
                response.raise_for_status()
                existing_categories[row["category_code"]] = response.json()

        existing_products = {row["sku"]: row for row in client.get("/products?page_size=100").raise_for_status().json()["items"]}
        for row in read_csv("products.csv"):
            if row["sku"] in existing_products:
                continue
            response = client.post("/products", json={"sku": row["sku"], "name": row["name"], "category_id": existing_categories[row["category_code"]]["id"], "current_price": row["current_price"], "demo_data": True})
            response.raise_for_status()

        existing_touchpoints = {row["touchpoint_code"]: row for row in client.get("/touchpoints").raise_for_status().json()}
        for row in read_csv("touchpoints.csv"):
            if row["touchpoint_code"] in existing_touchpoints:
                continue
            response = client.post("/touchpoints", json={"touchpoint_code": row["touchpoint_code"], "name": row["name"], "sequence_order": int(row["sequence_order"]), "demo_data": True})
            response.raise_for_status()

        customers = {row["customer_code"]: row for row in client.get("/customers?page_size=100").raise_for_status().json()["items"]}
        products = {row["sku"]: row for row in client.get("/products?page_size=100").raise_for_status().json()["items"]}
        items_by_order = defaultdict(list)
        for row in read_csv("order_items.csv"):
            items_by_order[row["external_code"]].append({"product_id": products[row["sku"]]["id"], "quantity": int(row["quantity"]), "unit_price": row["unit_price"]})
        existing_orders = {row["external_code"] for row in client.get("/orders?page_size=100").raise_for_status().json()["items"]}
        for row in read_csv("orders.csv"):
            if row["external_code"] in existing_orders:
                continue
            response = client.post("/orders", json={"external_code": row["external_code"], "customer_id": customers[row["customer_code"]]["id"], "ordered_at": row["ordered_at"], "status": row["status"], "items": items_by_order[row["external_code"]], "demo_data": True})
            response.raise_for_status()
    print("Đã tạo dữ liệu CRM mô phỏng")


if __name__ == "__main__":
    main()

