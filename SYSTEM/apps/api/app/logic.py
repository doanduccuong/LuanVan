from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models import (
    Customer,
    FaceTemplate,
    Order,
    OrderItem,
    Product,
    RecordStatus,
    Visit,
    VisitStatus,
)


def ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise HTTPException(status_code=422, detail="Thời gian phải có múi giờ")
    return value.astimezone(timezone.utc)


def cosine_distance(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("Hai véc-tơ phải có cùng số chiều")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        raise ValueError("Véc-tơ không được bằng không")
    return 1.0 - dot / (norm_a * norm_b)


def load_face_threshold(path: Path | None = None) -> tuple[float, str] | None:
    artifact_path = path or get_settings().face_threshold_artifact_path
    if not artifact_path.exists():
        return None
    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    threshold = data.get("threshold")
    version = data.get("version")
    if not isinstance(threshold, (int, float)) or not isinstance(version, str):
        return None
    return float(threshold), version


def match_customer(db: Session, embedding: list[float]) -> tuple[Customer | None, float | None, str]:
    threshold_data = load_face_threshold()
    if threshold_data is None:
        return None, None, "DISABLED"
    threshold, _version = threshold_data
    templates = db.scalars(
        select(FaceTemplate)
        .join(Customer)
        .where(
            FaceTemplate.active.is_(True),
            Customer.face_consent.is_(True),
            Customer.status == RecordStatus.ACTIVE,
        )
    ).all()
    best_template = None
    best_distance = None
    for template in templates:
        distance = cosine_distance(embedding, list(template.embedding))
        if best_distance is None or distance < best_distance:
            best_template = template
            best_distance = distance
    if best_template is None or best_distance is None or best_distance > threshold:
        return None, best_distance, "NO_MATCH"
    return db.get(Customer, best_template.customer_id), best_distance, "MATCHED"


def get_or_create_visit(db: Session, customer: Customer, observed_at: datetime, demo_data: bool) -> Visit:
    observed_at = ensure_aware(observed_at)
    settings = get_settings()
    active = db.scalar(
        select(Visit).where(Visit.customer_id == customer.id, Visit.status == VisitStatus.ACTIVE)
    )
    if active:
        last_seen = active.last_seen_at
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        if observed_at >= last_seen and observed_at - last_seen <= timedelta(seconds=settings.visit_idle_timeout_seconds):
            active.last_seen_at = observed_at
            return active
        if observed_at >= last_seen:
            active.status = VisitStatus.CLOSED
            active.ended_at = last_seen
            active.close_reason = "TIMEOUT"
            db.flush()
    visit = Visit(
        customer_id=customer.id,
        started_at=observed_at,
        last_seen_at=observed_at,
        status=VisitStatus.ACTIVE,
        demo_data=demo_data,
    )
    db.add(visit)
    db.flush()
    return visit


def create_order_items(db: Session, order: Order, requested_items: list[dict]) -> None:
    total = Decimal("0")
    for item in requested_items:
        product = db.get(Product, item["product_id"])
        if not product:
            raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
        if product.status != RecordStatus.ACTIVE:
            raise HTTPException(status_code=409, detail=f"Sản phẩm {product.sku} đã ngừng kinh doanh")
        quantity = int(item["quantity"])
        if quantity <= 0:
            raise HTTPException(status_code=422, detail="Số lượng phải lớn hơn 0")
        unit_price = Decimal(str(item.get("unit_price") or product.current_price))
        line_total = unit_price * quantity
        total += line_total
        order.items.append(
            OrderItem(
                product_id=product.id,
                product_code_snapshot=product.sku,
                product_name_snapshot=product.name,
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )
    order.total_amount = total

