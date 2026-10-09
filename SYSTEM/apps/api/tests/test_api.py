from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Role, User
from app.security import hash_password
from app.vision_client import VisionFaceResult, VisionResult, get_vision_client


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


def test_simulated_observations_are_marked_and_form_a_closed_visit():
    client = make_client()
    suffix = datetime.now(timezone.utc).strftime("%H%M%S%f")
    customer = client.post(
        "/api/v1/customers",
        json={
            "customer_code": f"SIM-CUS-{suffix}",
            "full_name": "Khách mô phỏng",
            "profile_image_url": "/demo/customers/CUS-DEMO-001.jpg",
        },
    ).json()
    touchpoint = client.post(
        "/api/v1/touchpoints",
        json={
            "touchpoint_code": f"SIM-TP-{suffix}",
            "name": "Điểm chạm mô phỏng",
            "sequence_order": int(suffix[-7:]),
        },
    ).json()
    observed_at = datetime.now(timezone.utc).isoformat()
    response = client.post(
        "/api/v1/simulation/observations/batch",
        json={
            "observations": [
                {
                    "event_id": f"SIM-EVENT-{suffix}",
                    "simulation_run_id": f"SIM-RUN-{suffix}",
                    "touchpoint_id": touchpoint["id"],
                    "customer_id": customer["id"],
                    "observed_at": observed_at,
                    "expression_label": "Happy",
                    "expression_confidence": 0.9,
                    "end_of_visit": True,
                }
            ]
        },
    )
    assert response.status_code == 201, response.text
    visit_id = response.json()["items"][0]["visit_id"]
    detail = client.get(f"/api/v1/visits/{visit_id}").json()
    assert detail["visit"]["status"] == "CLOSED"
    assert detail["observations"][0]["source_type"] == "SIMULATOR"
    assert detail["observations"][0]["simulation_run_id"] == f"SIM-RUN-{suffix}"

    timeline = client.get(
        "/api/v1/reports/expression-timeline",
        params={"touchpoint_id": touchpoint["id"], "bucket_minutes": 15},
    )
    assert timeline.status_code == 200, timeline.text
    timeline_rows = timeline.json()
    assert any(row["label"] == "Happy" and row["count"] >= 1 for row in timeline_rows)
    assert all(row["touchpoint_id"] == touchpoint["id"] for row in timeline_rows)

    invalid_event_id = f"SIM-INVALID-{suffix}"
    invalid = client.post(
        "/api/v1/simulation/observations/batch",
        json={
            "observations": [
                {
                    "event_id": invalid_event_id,
                    "simulation_run_id": f"SIM-RUN-{suffix}",
                    "touchpoint_id": touchpoint["id"],
                    "observed_at": observed_at,
                    "image_status": "INVALID_IMAGE",
                    "expression_status": "NOT_RUN",
                    "identity_status": "NOT_RUN",
                }
            ]
        },
    )
    assert invalid.status_code == 201, invalid.text
    assert invalid.json()["items"][0]["observation_id"] is None
    unidentified = client.get("/api/v1/observations", params={"customer_scope": "unidentified", "page_size": 100}).json()
    assert invalid_event_id not in {row["event_id"] for row in unidentified["items"]}


def test_missing_area_manual_assignment_filters_and_revision_history():
    client = make_client()
    suffix = datetime.now(timezone.utc).strftime("%H%M%S%f")
    sequence = int(suffix[-8:]) * 10
    customer = client.post(
        "/api/v1/customers",
        json={"customer_code": f"FLOW-CUS-{suffix}", "full_name": "Khách kiểm thử luồng"},
    ).json()
    areas = []
    for index, name in enumerate(("Khu vực đầu", "Khu vực giữa", "Khu vực cuối")):
        response = client.post(
            "/api/v1/touchpoints",
            json={"touchpoint_code": f"FLOW-{index}-{suffix}", "name": name, "sequence_order": sequence + index},
        )
        assert response.status_code == 201, response.text
        areas.append(response.json())
    started = datetime.now(timezone.utc)
    run_id = f"FLOW-RUN-{suffix}"
    batch = client.post(
        "/api/v1/simulation/observations/batch",
        json={
            "observations": [
                {
                    "event_id": f"FLOW-1-{suffix}",
                    "simulation_run_id": run_id,
                    "touchpoint_id": areas[0]["id"],
                    "customer_id": customer["id"],
                    "observed_at": started.isoformat(),
                    "expression_label": "Neutral",
                    "expression_confidence": 0.7,
                },
                {
                    "event_id": f"FLOW-2-{suffix}",
                    "simulation_run_id": run_id,
                    "touchpoint_id": areas[2]["id"],
                    "customer_id": customer["id"],
                    "observed_at": (started + timedelta(minutes=2)).isoformat(),
                    "expression_label": "Happy",
                    "expression_confidence": 0.9,
                    "end_of_visit": True,
                },
                {
                    "event_id": f"FLOW-UNKNOWN-{suffix}",
                    "simulation_run_id": run_id,
                    "touchpoint_id": areas[1]["id"],
                    "customer_id": None,
                    "observed_at": (started + timedelta(minutes=1)).isoformat(),
                    "expression_label": "Surprise",
                    "expression_confidence": 0.8,
                    "identity_status": "NO_MATCH",
                },
            ]
        },
    )
    assert batch.status_code == 201, batch.text
    visit_id = batch.json()["items"][0]["visit_id"]
    unknown_id = batch.json()["items"][2]["observation_id"]

    analysis = client.get(f"/api/v1/visits/{visit_id}/analysis")
    assert analysis.status_code == 200, analysis.text
    assert [row["name"] for row in analysis.json()["missing_touchpoints"]] == ["Khu vực giữa"]

    unidentified = client.get("/api/v1/reports/expression-distribution", params={"customer_scope": "unidentified"}).json()
    assert any(row["touchpoint_id"] == areas[1]["id"] and row["label"] == "Surprise" for row in unidentified)
    registered = client.get("/api/v1/reports/expression-distribution", params={"customer_scope": "registered"}).json()
    assert not any(row["touchpoint_id"] == areas[1]["id"] and row["label"] == "Surprise" for row in registered)

    changes = client.get("/api/v1/reports/expression-changes").json()
    relevant = [row for row in changes if row["from_touchpoint_id"] == areas[0]["id"] and row["to_touchpoint_id"] == areas[2]["id"]]
    assert relevant and relevant[0]["percentage"] == 1.0

    assignment = client.patch(f"/api/v1/observations/{unknown_id}/customer", json={"customer_id": customer["id"]})
    assert assignment.status_code == 200, assignment.text
    assert assignment.json()["identity_status"] == "MANUALLY_ASSIGNED"
    revisions = client.get(f"/api/v1/observations/{unknown_id}/revisions").json()
    assert len(revisions) == 1
    assert revisions[0]["snapshot"]["identity_status"] == "NO_MATCH"

def test_invalid_observation_request_is_visible_in_quality_report():
    client = make_client()
    response = client.post(
        "/api/v1/observations",
        data={"event_id": "invalid-input-test", "observed_at": datetime.now(timezone.utc).isoformat()},
    )
    assert response.status_code == 422
    quality = client.get("/api/v1/reports/data-quality-summary").json()
    assert any(row["issue_code"] == "MISSING_TOUCHPOINT" and row["count"] >= 1 for row in quality["ingestion_issues"])


def test_one_capture_creates_one_observation_per_detected_face():
    class MultiFaceVisionClient:
        async def analyze(self, _image: bytes, _filename: str, _content_type: str | None) -> VisionResult:
            faces = [
                VisionFaceResult(
                    face_index=index,
                    image_status="VALID",
                    box=[float(index * 100), 0.0, float(index * 100 + 80), 80.0],
                    expression_status="VALID",
                    identity_status="VALID",
                    expression_label="Happy" if index == 0 else "Neutral",
                    expression_confidence=0.9,
                    expression_scores=None,
                    embedding=[1.0 if position == index else 0.0 for position in range(512)],
                    detection_score=0.98,
                )
                for index in range(2)
            ]
            return VisionResult(
                image_status="VALID",
                face_count=2,
                faces=faces,
                models={"detector": "test", "emotion": "test", "embedding": "test"},
            )

    client = make_client()
    suffix = datetime.now(timezone.utc).strftime("%H%M%S%f")
    touchpoint = client.post(
        "/api/v1/touchpoints",
        json={
            "touchpoint_code": f"MULTI-TP-{suffix}",
            "name": "Khu vực nhiều khách",
            "sequence_order": int(suffix[-8:]),
        },
    ).json()
    app.dependency_overrides[get_vision_client] = lambda: MultiFaceVisionClient()
    try:
        payload = {
            "event_id": f"MULTI-EVENT-{suffix}",
            "touchpoint_id": touchpoint["id"],
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
        response = client.post(
            "/api/v1/observations",
            data=payload,
            files={"image": ("frame.jpg", b"test-frame", "image/jpeg")},
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["image_status"] == "VALID"
        assert body["face_count"] == 2
        assert [item["face_index"] for item in body["observations"]] == [0, 1]
        assert [item["expression_label"] for item in body["observations"]] == ["Happy", "Neutral"]
        assert len({item["capture_event_id"] for item in body["observations"]}) == 1

        repeated = client.post(
            "/api/v1/observations",
            data=payload,
            files={"image": ("frame.jpg", b"test-frame", "image/jpeg")},
        )
        assert repeated.status_code == 201
        assert [item["id"] for item in repeated.json()["observations"]] == [item["id"] for item in body["observations"]]
    finally:
        app.dependency_overrides.pop(get_vision_client, None)


def test_sequence_analysis_persists_clusters_medoids_and_assignments():
    client = make_client()
    suffix = datetime.now(timezone.utc).strftime("%H%M%S%f")
    base_order = int(suffix[-7:]) * 10
    touchpoints = []
    for index, name in enumerate(("Cửa vào", "Trưng bày", "Tư vấn", "Thanh toán")):
        response = client.post(
            "/api/v1/touchpoints",
            json={
                "touchpoint_code": f"SEQ-{index}-{suffix}",
                "name": name,
                "sequence_order": base_order + index,
            },
        )
        assert response.status_code == 201, response.text
        touchpoints.append(response.json())

    run_id = f"SEQ-RUN-{suffix}"
    started = datetime.now(timezone.utc)
    observations = []
    patterns = [
        ["Neutral", "Happy", "Happy", "Happy"],
        ["Sad", "Sad", "Angry", "Angry"],
    ]
    for customer_index in range(8):
        customer = client.post(
            "/api/v1/customers",
            json={
                "customer_code": f"SEQ-CUS-{customer_index}-{suffix}",
                "full_name": f"Khách chuỗi {customer_index}",
            },
        ).json()
        pattern = patterns[customer_index // 4]
        for event_index, (touchpoint, label) in enumerate(zip(touchpoints, pattern, strict=True)):
            observations.append(
                {
                    "event_id": f"SEQ-{customer_index}-{event_index}-{suffix}",
                    "simulation_run_id": run_id,
                    "touchpoint_id": touchpoint["id"],
                    "customer_id": customer["id"],
                    "observed_at": (started + timedelta(hours=customer_index, minutes=event_index * 5)).isoformat(),
                    "expression_label": label,
                    "expression_confidence": 0.9,
                    "end_of_visit": event_index == 3,
                }
            )
    batch = client.post("/api/v1/simulation/observations/batch", json={"observations": observations})
    assert batch.status_code == 201, batch.text

    analysis = client.post(
        "/api/v1/sequence-analyses",
        json={
            "source_type": "SIMULATOR",
            "source_run_id": run_id,
            "min_states": 4,
            "min_cluster_size_abs": 2,
            "min_cluster_ratio": 0.1,
            "k_max": 2,
            "random_state": 7,
        },
    )
    assert analysis.status_code == 201, analysis.text
    result = analysis.json()
    assert result["status"] == "COMPLETED"
    assert result["received_visit_count"] == 8
    assert result["used_visit_count"] == 8
    assert result["selected_k"] == 2
    assert result["average_silhouette_width"] == pytest.approx(1.0)

    clusters = client.get(f"/api/v1/sequence-analyses/{result['id']}/clusters").json()
    assert sorted(cluster["size"] for cluster in clusters) == [4, 4]
    assignments = client.get(f"/api/v1/sequence-analyses/{result['id']}/assignments").json()
    assert assignments["total"] == 8
    assert all(item["customer"] for item in assignments["items"])
    assert all(len(item["sequence"]) == 4 for item in assignments["items"])
