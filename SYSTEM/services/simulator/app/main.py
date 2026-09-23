from __future__ import annotations

import os
import random
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000/api/v1").rstrip("/")
MANAGER_EMAIL = os.getenv("INITIAL_USER_EMAIL", "manager@example.com")
MANAGER_PASSWORD = os.getenv("INITIAL_USER_PASSWORD", "demo1234")
CUSTOMER_COUNT = 100
LABELS = ("Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral")

# Các trọng số dưới đây chỉ tạo dữ liệu trình diễn có thể lặp lại theo seed.
# Chúng không phải kết quả nghiên cứu và không dùng để đánh giá mô hình FER.
TOUCHPOINT_WEIGHTS = {
    "TP-ENTRANCE": (4, 1, 3, 18, 5, 12, 28),
    "TP-DISPLAY": (5, 2, 4, 24, 6, 15, 25),
    "TP-CONSULT": (4, 1, 5, 28, 5, 12, 22),
    "TP-CHECKOUT": (7, 2, 4, 25, 8, 8, 24),
}


class RunInput(BaseModel):
    customer_count: int = Field(default=CUSTOMER_COUNT, ge=CUSTOMER_COUNT, le=CUSTOMER_COUNT)
    seed: int = 20260923


class RunResult(BaseModel):
    run_id: str
    customer_count: int
    visit_count: int
    observation_count: int
    order_count: int
    error_observation_count: int


app = FastAPI(title="Touchpoint journey simulator", version="0.1.0")


def login(client: httpx.Client) -> None:
    response = client.post("/auth/login", json={"email": MANAGER_EMAIL, "password": MANAGER_PASSWORD})
    response.raise_for_status()


def choose_expression(rng: random.Random, touchpoint_code: str, previous: str | None) -> str:
    if previous and rng.random() < 0.42:
        return previous
    return rng.choices(LABELS, weights=TOUCHPOINT_WEIGHTS[touchpoint_code], k=1)[0]


@app.get("/health/live")
def health_live():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=10) as client:
            login(client)
            client.get("/touchpoints").raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="API CRM chưa sẵn sàng") from exc
    return {"status": "ready"}


@app.post("/api/v1/runs", response_model=RunResult, status_code=201)
def create_run(payload: RunInput):
    rng = random.Random(payload.seed)
    run_id = f"SIM-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{uuid.uuid4().hex[:6]}"
    start = datetime(2026, 9, 23, 8, 0, tzinfo=timezone(timedelta(hours=7)))

    try:
        with httpx.Client(base_url=API_BASE_URL, timeout=60) as client:
            login(client)
            customers_page = client.get("/customers", params={"page_size": 100}).raise_for_status().json()
            customers = sorted(
                [row for row in customers_page["items"] if row["customer_code"].startswith("CUS-DEMO-")],
                key=lambda row: row["customer_code"],
            )
            if len(customers) != CUSTOMER_COUNT:
                raise HTTPException(
                    status_code=409,
                    detail=f"Cần đúng {CUSTOMER_COUNT} khách hàng demo, hiện có {len(customers)}",
                )
            touchpoints = sorted(client.get("/touchpoints").raise_for_status().json(), key=lambda row: row["sequence_order"])
            products = client.get("/products", params={"page_size": 100}).raise_for_status().json()["items"]
            if len(touchpoints) < 4 or len(products) < 12:
                raise HTTPException(status_code=409, detail="Cần tạo dữ liệu điểm chạm và sản phẩm trước khi mô phỏng")

            observations: list[dict] = []
            order_plans: list[dict] = []
            visit_count = 0
            for customer_index, customer in enumerate(customers):
                customer_visits = 2 if customer_index % 4 == 0 else 1
                for visit_index in range(customer_visits):
                    visit_count += 1
                    visit_time = start + timedelta(days=customer_index // 10, minutes=customer_index * 7 + visit_index * 180)
                    stop_count = rng.choice((2, 3, 4))
                    selected = [touchpoints[0], *rng.sample(touchpoints[1:-1], k=max(0, stop_count - 2)), touchpoints[-1]]
                    selected.sort(key=lambda row: row["sequence_order"])
                    previous = None
                    event_ids: list[str] = []
                    observed_time = visit_time
                    for stop_index, touchpoint in enumerate(selected):
                        if stop_index:
                            observed_time += timedelta(minutes=rng.randint(4, 9))
                        label = choose_expression(rng, touchpoint["touchpoint_code"], previous)
                        previous = label
                        event_id = f"{run_id}-{customer_index + 1:03d}-{visit_index + 1}-{stop_index + 1}"
                        event_ids.append(event_id)
                        observations.append(
                            {
                                "event_id": event_id,
                                "simulation_run_id": run_id,
                                "touchpoint_id": touchpoint["id"],
                                "customer_id": customer["id"],
                                "observed_at": observed_time.isoformat(),
                                "expression_label": label,
                                "expression_confidence": round(rng.uniform(0.62, 0.97), 3),
                                "image_status": "VALID",
                                "expression_status": "VALID",
                                "identity_status": "MATCHED",
                                "end_of_visit": stop_index == len(selected) - 1,
                            }
                        )
                    if rng.random() < 0.72:
                        item_count = rng.randint(1, min(4, len(products)))
                        chosen_products = rng.sample(products, item_count)
                        order_plans.append(
                            {
                                "customer": customer,
                                "final_event_id": event_ids[-1],
                                "ordered_at": (visit_time + timedelta(minutes=len(selected) * 8 + 3)).isoformat(),
                                "items": [
                                    {"product_id": product["id"], "quantity": rng.randint(1, 3)}
                                    for product in chosen_products
                                ],
                            }
                        )

            error_count = 12
            for index in range(error_count):
                touchpoint = touchpoints[index % len(touchpoints)]
                observations.append(
                    {
                        "event_id": f"{run_id}-ERROR-{index + 1:02d}",
                        "simulation_run_id": run_id,
                        "touchpoint_id": touchpoint["id"],
                        "customer_id": None,
                        "observed_at": (start + timedelta(days=11, minutes=index)).isoformat(),
                        "expression_label": None,
                        "expression_confidence": None,
                        "image_status": "NO_FACE" if index < 8 else "INVALID_IMAGE",
                        "expression_status": "NOT_RUN",
                        "identity_status": "NOT_RUN",
                        "end_of_visit": False,
                    }
                )

            ingestion = client.post("/simulation/observations/batch", json={"observations": observations})
            ingestion.raise_for_status()
            visits_by_event = {row["event_id"]: row["visit_id"] for row in ingestion.json()["items"]}
            order_count = 0
            for order_index, plan in enumerate(order_plans, 1):
                order = client.post(
                    "/orders",
                    json={
                        "external_code": f"ORD-{run_id}-{order_index:03d}",
                        "customer_id": plan["customer"]["id"],
                        "visit_id": visits_by_event[plan["final_event_id"]],
                        "ordered_at": plan["ordered_at"],
                        "status": "COMPLETED",
                        "items": plan["items"],
                        "demo_data": True,
                    },
                )
                order.raise_for_status()
                order_count += 1
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500] if exc.response is not None else str(exc)
        raise HTTPException(status_code=502, detail=f"API CRM từ chối dữ liệu mô phỏng: {detail}") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Không kết nối được API CRM") from exc

    return RunResult(
        run_id=run_id,
        customer_count=CUSTOMER_COUNT,
        visit_count=visit_count,
        observation_count=len(observations),
        order_count=order_count,
        error_observation_count=error_count,
    )
