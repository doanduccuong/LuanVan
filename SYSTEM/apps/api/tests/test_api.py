from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Role, User
from app.security import hash_password


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
Base.metadata.create_all(engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db


def make_client() -> TestClient:
    with TestingSession() as db:
        if not db.query(User).filter(User.email == "test@example.com").first():
            db.add(User(email="test@example.com", password_hash=hash_password("test-password"), full_name="Test Manager", role=Role.MANAGER))
            db.commit()
    client = TestClient(app)
    response = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "test-password"})
    assert response.status_code == 200
    return client


def test_crm_product_order_history_keeps_price_snapshot():
    client = make_client()
    suffix = datetime.now(timezone.utc).strftime("%H%M%S%f")
    customer = client.post("/api/v1/customers", json={"customer_code": f"CUS-{suffix}", "full_name": "Khách kiểm thử"}).json()
    category_response = client.post("/api/v1/product-categories", json={"category_code": f"CAT-{suffix}", "name": "Nhóm kiểm thử"})
    assert category_response.status_code == 201
    category = category_response.json()
    product_response = client.post("/api/v1/products", json={"sku": f"SKU-{suffix}", "name": "Sản phẩm kiểm thử", "category_id": category["id"], "current_price": "12000"})
    assert product_response.status_code == 201
    product = product_response.json()
    order_response = client.post(
        "/api/v1/orders",
        json={
            "external_code": f"ORD-{suffix}",
            "customer_id": customer["id"],
            "ordered_at": datetime.now(timezone.utc).isoformat(),
            "status": "COMPLETED",
            "items": [{"product_id": product["id"], "quantity": 2}],
        },
    )
    assert order_response.status_code == 201, order_response.text
    order = order_response.json()
    assert float(order["total_amount"]) == 24000
    assert float(order["items"][0]["unit_price"]) == 12000

    assert client.patch(f"/api/v1/products/{product['id']}", json={"current_price": "18000"}).status_code == 200
    historical = client.get(f"/api/v1/orders/{order['id']}").json()
    assert float(historical["items"][0]["unit_price"]) == 12000
    assert historical["items"][0]["product_name_snapshot"] == "Sản phẩm kiểm thử"


def test_touchpoints_are_global_for_single_store():
    client = make_client()
    suffix = datetime.now(timezone.utc).strftime("%H%M%S%f")
    response = client.post("/api/v1/touchpoints", json={"touchpoint_code": f"TP-{suffix}", "name": "Điểm chạm kiểm thử", "sequence_order": int(suffix[-5:])})
    assert response.status_code == 201, response.text
    payload = response.json()
    assert "store_id" not in payload
