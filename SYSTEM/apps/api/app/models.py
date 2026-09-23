from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"


class RecordStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class VisitStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class OrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False), default=Role.MANAGER)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    customer_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[RecordStatus] = mapped_column(Enum(RecordStatus, native_enum=False), default=RecordStatus.ACTIVE)
    face_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    face_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    demo_data: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    face_templates: Mapped[list[FaceTemplate]] = relationship(back_populates="customer", cascade="all, delete-orphan")


embedding_type = Vector(512).with_variant(JSON(), "sqlite")


class FaceTemplate(Base):
    __tablename__ = "face_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    embedding: Mapped[list[float]] = mapped_column(embedding_type)
    model_name: Mapped[str] = mapped_column(String(64), default="ArcFace")
    model_version: Mapped[str] = mapped_column(String(255))
    quality_score: Mapped[float | None] = mapped_column(nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    customer: Mapped[Customer] = relationship(back_populates="face_templates")


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    category_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    demo_data: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("product_categories.id"), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[RecordStatus] = mapped_column(Enum(RecordStatus, native_enum=False), default=RecordStatus.ACTIVE)
    demo_data: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    category: Mapped[ProductCategory] = relationship()


class Touchpoint(Base):
    __tablename__ = "touchpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    touchpoint_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    sequence_order: Mapped[int] = mapped_column(Integer, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    demo_data: Mapped[bool] = mapped_column(Boolean, default=False, index=True)


class Visit(Base):
    __tablename__ = "visits"
    __table_args__ = (
        Index(
            "uq_active_visit_customer",
            "customer_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
            sqlite_where=text("status = 'ACTIVE'"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[VisitStatus] = mapped_column(Enum(VisitStatus, native_enum=False), default=VisitStatus.ACTIVE, index=True)
    close_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
    demo_data: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    customer: Mapped[Customer] = relationship()


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    touchpoint_id: Mapped[str] = mapped_column(ForeignKey("touchpoints.id"), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)
    visit_id: Mapped[str | None] = mapped_column(ForeignKey("visits.id"), nullable=True, index=True)
    expression_label: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    expression_confidence: Mapped[float | None] = mapped_column(nullable=True)
    expression_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    face_match_distance: Mapped[float | None] = mapped_column(nullable=True)
    image_status: Mapped[str] = mapped_column(String(32), default="NOT_RUN", index=True)
    expression_status: Mapped[str] = mapped_column(String(32), default="NOT_RUN", index=True)
    identity_status: Mapped[str] = mapped_column(String(32), default="NOT_RUN", index=True)
    detector_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emotion_model_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recognition_model_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(32), default="CAMERA", index=True)
    simulation_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    demo_data: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    touchpoint: Mapped[Touchpoint] = relationship()
    customer: Mapped[Customer | None] = relationship()


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    external_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    visit_id: Mapped[str | None] = mapped_column(ForeignKey("visits.id"), nullable=True, index=True)
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, native_enum=False), default=OrderStatus.DRAFT, index=True)
    demo_data: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    customer: Mapped[Customer] = relationship()
    items: Mapped[list[OrderItem]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    product_code_snapshot: Mapped[str] = mapped_column(String(64))
    product_name_snapshot: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    order: Mapped[Order] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
