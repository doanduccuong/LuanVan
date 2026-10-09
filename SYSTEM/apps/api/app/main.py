from __future__ import annotations

import hashlib
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .logic import create_order_items, ensure_aware, find_visit_for_order, get_or_create_visit, load_face_threshold, match_customer
from .models import (
    AuditLog,
    CaptureEvent,
    Customer,
    FaceTemplate,
    IngestionIssue,
    Observation,
    ObservationRevision,
    Order,
    OrderStatus,
    Product,
    ProductCategory,
    RecordStatus,
    Role,
    SequenceAnalysisRun,
    SequenceClusterAssignment,
    SequenceClusterSummary,
    Touchpoint,
    User,
    Visit,
    VisitStatus,
)
from .sequence_analysis import (
    ALGORITHM_VERSION,
    PREPROCESSING_VERSION,
    AnalysisConfig,
    SequenceAnalysisError,
    SequenceObservation,
    cluster_visit_sequences,
    prepare_visit_sequences,
)
from .security import create_access_token, get_current_user, hash_password, require_roles, verify_password
from .vision_client import VisionClient, get_vision_client


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class CustomerInput(BaseModel):
    customer_code: str = Field(min_length=1, max_length=64)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = None
    email: EmailStr | None = None
    profile_image_url: str | None = Field(default=None, max_length=512)
    face_consent: bool = False
    demo_data: bool = False


class CustomerPatch(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    profile_image_url: str | None = Field(default=None, max_length=512)
    status: RecordStatus | None = None


class ConsentInput(BaseModel):
    consent: bool


class CategoryInput(BaseModel):
    category_code: str
    name: str
    description: str | None = None
    active: bool = True
    demo_data: bool = False


class CategoryPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None


class ProductInput(BaseModel):
    sku: str
    name: str
    category_id: str
    description: str | None = None
    current_price: Decimal = Field(ge=0)
    status: RecordStatus = RecordStatus.ACTIVE
    demo_data: bool = False


class ProductPatch(BaseModel):
    name: str | None = None
    category_id: str | None = None
    description: str | None = None
    current_price: Decimal | None = Field(default=None, ge=0)
    status: RecordStatus | None = None


class TouchpointInput(BaseModel):
    touchpoint_code: str
    name: str
    sequence_order: int = Field(ge=0)
    active: bool = True
    demo_data: bool = False


class TouchpointPatch(BaseModel):
    name: str | None = None
    sequence_order: int | None = Field(default=None, ge=0)
    active: bool | None = None


class OrderItemInput(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)


class OrderInput(BaseModel):
    external_code: str
    customer_id: str
    visit_id: str | None = None
    ordered_at: datetime
    status: OrderStatus = OrderStatus.CONFIRMED
    items: list[OrderItemInput] = Field(min_length=1)
    demo_data: bool = False


class OrderStatusInput(BaseModel):
    status: OrderStatus


class ReprocessReasonInput(BaseModel):
    reason: str = Field(default="MANUAL_REPROCESS", min_length=1, max_length=64)


EXPRESSION_LABELS = {"Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"}


class SimulatedObservationInput(BaseModel):
    event_id: str = Field(min_length=1, max_length=128)
    simulation_run_id: str = Field(min_length=1, max_length=64)
    touchpoint_id: str
    customer_id: str | None = None
    observed_at: datetime
    expression_label: str | None = None
    expression_confidence: float | None = Field(default=None, ge=0, le=1)
    image_status: str = "VALID"
    expression_status: str = "VALID"
    identity_status: str = "MATCHED"
    end_of_visit: bool = False


class SimulatedObservationBatchInput(BaseModel):
    observations: list[SimulatedObservationInput] = Field(min_length=1, max_length=2000)


class SequenceAnalysisInput(BaseModel):
    source_type: str = Field(pattern="^(CAMERA|SIMULATOR)$")
    source_run_id: str = Field(min_length=1, max_length=64)
    min_states: int = Field(default=3, ge=2, le=20)
    min_cluster_size_abs: int = Field(default=2, ge=2)
    min_cluster_ratio: float = Field(default=0.05, gt=0, le=0.5)
    k_min: int = Field(default=2, ge=2)
    k_max: int | None = Field(default=None, ge=2)
    asw_tolerance: float = Field(default=0.02, ge=0, le=0.2)
    random_state: int = 42


class SequenceClusterPatch(BaseModel):
    display_name: str | None = Field(default=None, max_length=255)


def to_dict(obj, *fields: str) -> dict:
    return {field: getattr(obj, field) for field in fields}


def audit(db: Session, user: User | None, action: str, entity_type: str, entity_id: str | None, details: dict | None = None) -> None:
    db.add(
        AuditLog(
            actor_user_id=user.id if user else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            request_id=str(uuid.uuid4()),
            details=details or {},
        )
    )


OBSERVATION_SNAPSHOT_FIELDS = (
    "customer_id",
    "visit_id",
    "expression_label",
    "expression_confidence",
    "expression_scores",
    "face_match_distance",
    "bounding_box",
    "detection_score",
    "image_status",
    "expression_status",
    "identity_status",
    "detector_version",
    "emotion_model_version",
    "recognition_model_version",
)


def save_observation_revision(db: Session, observation: Observation, reason: str, user: User | None) -> ObservationRevision:
    number = (db.scalar(select(func.max(ObservationRevision.revision_number)).where(ObservationRevision.observation_id == observation.id)) or 0) + 1
    revision = ObservationRevision(
        observation_id=observation.id,
        revision_number=number,
        reason=reason,
        snapshot=jsonable_encoder(to_dict(observation, *OBSERVATION_SNAPSHOT_FIELDS)),
        created_by=user.id if user else None,
    )
    db.add(revision)
    return revision


def record_ingestion_issue(
    db: Session,
    *,
    event_id: str | None,
    touchpoint_reference: str | None,
    observed_at_text: str | None,
    issue_code: str,
    detail: str,
) -> None:
    db.add(
        IngestionIssue(
            event_id=event_id,
            touchpoint_reference=touchpoint_reference,
            observed_at_text=observed_at_text,
            issue_code=issue_code,
            detail=detail,
        )
    )
    db.commit()


def parse_observed_at(value: str | None) -> datetime:
    if not value:
        raise ValueError("Thiếu thời gian ghi nhận")
    try:
        return ensure_aware(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except (ValueError, TypeError) as exc:
        raise ValueError("Thời gian ghi nhận không hợp lệ hoặc thiếu múi giờ") from exc


def attach_visit(db: Session, customer: Customer, observed_at: datetime, demo_data: bool) -> Visit:
    existing = find_visit_for_order(db, customer.id, observed_at)
    if existing:
        return existing
    active = db.scalar(select(Visit).where(Visit.customer_id == customer.id, Visit.status == VisitStatus.ACTIVE))
    if active:
        active_start = active.started_at.replace(tzinfo=timezone.utc) if active.started_at.tzinfo is None else active.started_at.astimezone(timezone.utc)
        if observed_at < active_start:
            historical = Visit(
                customer_id=customer.id,
                started_at=observed_at,
                last_seen_at=observed_at,
                ended_at=observed_at,
                status=VisitStatus.CLOSED,
                close_reason="HISTORICAL_ASSIGNMENT",
                demo_data=demo_data,
            )
            db.add(historical)
            db.flush()
            return historical
    return get_or_create_visit(db, customer, observed_at, demo_data)


def seed_initial_user() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        email = settings.initial_user_email.lower()
        if db.scalar(select(User).where(User.email == email)):
            return
        db.add(
            User(
                email=email,
                password_hash=hash_password(settings.initial_user_password),
                full_name="Quản lý hệ thống",
                role=Role.MANAGER,
            )
        )
        db.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    seed_initial_user()
    yield


app = FastAPI(title="Touchpoint CRM API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health/live")
def health_live():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    db.scalar(select(func.count()).select_from(User))
    return {"status": "ready"}


@app.post("/api/v1/auth/login")
def login(payload: LoginInput, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower(), User.active.is_(True)))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    token = create_access_token(user)
    settings = get_settings()
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.access_token_ttl_seconds,
    )
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}


@app.post("/api/v1/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@app.get("/api/v1/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}


@app.get("/api/v1/customers")
def list_customers(
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    stmt = select(Customer)
    count_stmt = select(func.count()).select_from(Customer)
    if search:
        pattern = f"%{search}%"
        condition = or_(Customer.customer_code.ilike(pattern), Customer.full_name.ilike(pattern), Customer.phone.ilike(pattern))
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.order_by(Customer.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": rows, "page": page, "page_size": page_size, "total": total}


@app.post("/api/v1/customers", status_code=201)
def create_customer(payload: CustomerInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    customer = Customer(
        customer_code=payload.customer_code.strip(),
        full_name=payload.full_name.strip(),
        phone=payload.phone,
        email=str(payload.email).lower() if payload.email else None,
        profile_image_url=payload.profile_image_url,
        face_consent=payload.face_consent,
        face_consent_at=datetime.now(timezone.utc) if payload.face_consent else None,
        demo_data=payload.demo_data,
    )
    db.add(customer)
    audit(db, user, "CUSTOMER_CREATED", "customer", customer.id)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Mã khách hàng đã tồn tại") from exc
    db.refresh(customer)
    return customer


@app.get("/api/v1/customers/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    return customer


@app.patch("/api/v1/customers/{customer_id}")
def patch_customer(payload: CustomerPatch, customer_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(customer, key, str(value).lower() if key == "email" and value else value)
    audit(db, user, "CUSTOMER_UPDATED", "customer", customer.id)
    db.commit()
    db.refresh(customer)
    return customer


@app.put("/api/v1/customers/{customer_id}/face-consent")
def update_consent(payload: ConsentInput, customer_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN))):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    customer.face_consent = payload.consent
    customer.face_consent_at = datetime.now(timezone.utc) if payload.consent else None
    removed = 0
    if not payload.consent:
        for template in customer.face_templates:
            if template.active:
                template.active = False
                removed += 1
    audit(db, user, "FACE_CONSENT_CHANGED", "customer", customer.id, {"consent": payload.consent, "disabled_templates": removed})
    db.commit()
    return {"face_consent": customer.face_consent, "disabled_templates": removed}


async def read_image(upload: UploadFile) -> bytes:
    data = await upload.read()
    if not data or len(data) > get_settings().max_upload_bytes:
        raise HTTPException(status_code=422, detail="Ảnh rỗng hoặc vượt dung lượng cho phép")
    return data


@app.post("/api/v1/customers/{customer_id}/face-templates", status_code=201)
async def enroll_face(
    customer_id: str,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN)),
    vision: VisionClient = Depends(get_vision_client),
):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    if not customer.face_consent:
        raise HTTPException(status_code=409, detail="Khách hàng chưa đồng ý sử dụng dữ liệu khuôn mặt")
    result = await vision.analyze(await read_image(image), image.filename or "image.jpg", image.content_type)
    face = result.single_face()
    if result.image_status != "VALID" or not face or not face.embedding:
        status = "MULTIPLE_FACES" if result.face_count > 1 else result.image_status
        raise HTTPException(status_code=422, detail=f"Không thể tạo mẫu khuôn mặt: {status}")
    template = FaceTemplate(
        customer_id=customer.id,
        embedding=face.embedding,
        model_name="ArcFace",
        model_version=result.models.get("embedding", "unknown"),
        quality_score=face.detection_score,
        created_by=user.id,
    )
    db.add(template)
    audit(db, user, "FACE_TEMPLATE_CREATED", "customer", customer.id)
    db.commit()
    db.refresh(template)
    return {"id": template.id, "model_name": template.model_name, "model_version": template.model_version, "created_at": template.created_at}


@app.get("/api/v1/customers/{customer_id}/face-templates")
def list_face_templates(customer_id: str, db: Session = Depends(get_db), _user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN))):
    if not db.get(Customer, customer_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    templates = db.scalars(select(FaceTemplate).where(FaceTemplate.customer_id == customer_id).order_by(FaceTemplate.created_at.desc())).all()
    return [
        {"id": item.id, "model_name": item.model_name, "model_version": item.model_version, "quality_score": item.quality_score, "active": item.active, "created_at": item.created_at}
        for item in templates
    ]


@app.delete("/api/v1/customers/{customer_id}/face-templates/{template_id}", status_code=204)
def delete_face_template(customer_id: str, template_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN))):
    template = db.scalar(select(FaceTemplate).where(FaceTemplate.id == template_id, FaceTemplate.customer_id == customer_id))
    if not template:
        raise HTTPException(status_code=404, detail="Không tìm thấy mẫu khuôn mặt")
    db.delete(template)
    audit(db, user, "FACE_TEMPLATE_DELETED", "customer", customer_id, {"template_id": template_id})
    db.commit()
    return Response(status_code=204)


@app.post("/api/v1/customers/search-by-face")
async def search_customer_by_face(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN)),
    vision: VisionClient = Depends(get_vision_client),
):
    result = await vision.analyze(await read_image(image), image.filename or "image.jpg", image.content_type)
    face = result.single_face()
    if result.image_status != "VALID" or not face or not face.embedding:
        status = "MULTIPLE_FACES" if result.face_count > 1 else result.image_status
        return {"status": status, "customer": None}
    customer, distance, identity_status = match_customer(db, face.embedding)
    audit(db, user, "FACE_SEARCH", "customer", customer.id if customer else None, {"status": identity_status})
    db.commit()
    threshold = load_face_threshold()
    return {
        "status": identity_status,
        "customer": customer,
        "distance": distance,
        "threshold_version": threshold[1] if threshold else None,
    }


@app.get("/api/v1/product-categories")
def list_categories(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.scalars(select(ProductCategory).order_by(ProductCategory.name)).all()


@app.post("/api/v1/product-categories", status_code=201)
def create_category(payload: CategoryInput, db: Session = Depends(get_db), _user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN))):
    category = ProductCategory(**payload.model_dump())
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Mã nhóm sản phẩm đã tồn tại") from exc
    db.refresh(category)
    return category


@app.patch("/api/v1/product-categories/{category_id}")
def patch_category(payload: CategoryPatch, category_id: str, db: Session = Depends(get_db), _user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN))):
    category = db.get(ProductCategory, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhóm sản phẩm")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category


@app.get("/api/v1/products")
def list_products(
    search: str | None = None,
    category_id: str | None = None,
    status_value: RecordStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    stmt = select(Product).options(selectinload(Product.category))
    count_stmt = select(func.count()).select_from(Product)
    conditions = []
    if search:
        pattern = f"%{search}%"
        conditions.append(or_(Product.sku.ilike(pattern), Product.name.ilike(pattern)))
    if category_id:
        conditions.append(Product.category_id == category_id)
    if status_value:
        conditions.append(Product.status == status_value)
    if conditions:
        stmt = stmt.where(*conditions)
        count_stmt = count_stmt.where(*conditions)
    total = db.scalar(count_stmt) or 0
    products = db.scalars(stmt.order_by(Product.name).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": products, "page": page, "page_size": page_size, "total": total}


@app.post("/api/v1/products", status_code=201)
def create_product(payload: ProductInput, db: Session = Depends(get_db), _user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN))):
    if not db.get(ProductCategory, payload.category_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy nhóm sản phẩm")
    product = Product(**payload.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Mã sản phẩm đã tồn tại") from exc
    db.refresh(product)
    return product


@app.get("/api/v1/products/{product_id}")
def get_product(product_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    product = db.scalar(select(Product).options(selectinload(Product.category)).where(Product.id == product_id))
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return product


@app.patch("/api/v1/products/{product_id}")
def patch_product(payload: ProductPatch, product_id: str, db: Session = Depends(get_db), _user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN))):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@app.get("/api/v1/touchpoints")
def list_touchpoints(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return db.scalars(select(Touchpoint).order_by(Touchpoint.sequence_order)).all()


@app.post("/api/v1/touchpoints", status_code=201)
def create_touchpoint(payload: TouchpointInput, db: Session = Depends(get_db), _user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN))):
    touchpoint = Touchpoint(**payload.model_dump())
    db.add(touchpoint)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Mã hoặc thứ tự điểm chạm đã tồn tại") from exc
    db.refresh(touchpoint)
    return touchpoint


@app.get("/api/v1/touchpoints/{touchpoint_id}")
def get_touchpoint(touchpoint_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    touchpoint = db.get(Touchpoint, touchpoint_id)
    if not touchpoint:
        raise HTTPException(status_code=404, detail="Không tìm thấy điểm chạm")
    return touchpoint


@app.patch("/api/v1/touchpoints/{touchpoint_id}")
def patch_touchpoint(payload: TouchpointPatch, touchpoint_id: str, db: Session = Depends(get_db), _user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN))):
    touchpoint = db.get(Touchpoint, touchpoint_id)
    if not touchpoint:
        raise HTTPException(status_code=404, detail="Không tìm thấy điểm chạm")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(touchpoint, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Thứ tự điểm chạm đã tồn tại") from exc
    db.refresh(touchpoint)
    return touchpoint


@app.get("/api/v1/orders")
def list_orders(
    customer_id: str | None = None,
    status_value: OrderStatus | None = Query(None, alias="status"),
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    stmt = select(Order).options(selectinload(Order.items), selectinload(Order.customer))
    count_stmt = select(func.count()).select_from(Order)
    conditions = []
    if customer_id:
        conditions.append(Order.customer_id == customer_id)
    if status_value:
        conditions.append(Order.status == status_value)
    if from_time:
        conditions.append(Order.ordered_at >= ensure_aware(from_time))
    if to_time:
        conditions.append(Order.ordered_at <= ensure_aware(to_time))
    if conditions:
        stmt = stmt.where(*conditions)
        count_stmt = count_stmt.where(*conditions)
    total = db.scalar(count_stmt) or 0
    orders = db.scalars(stmt.order_by(Order.ordered_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": orders, "page": page, "page_size": page_size, "total": total}


@app.get("/api/v1/customers/{customer_id}/orders")
def customer_orders(
    customer_id: str,
    status_value: OrderStatus | None = Query(None, alias="status"),
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    if not db.get(Customer, customer_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    stmt = select(Order).options(selectinload(Order.items)).where(Order.customer_id == customer_id)
    if status_value:
        stmt = stmt.where(Order.status == status_value)
    if from_time:
        stmt = stmt.where(Order.ordered_at >= ensure_aware(from_time))
    if to_time:
        stmt = stmt.where(Order.ordered_at <= ensure_aware(to_time))
    return db.scalars(stmt.order_by(Order.ordered_at.desc())).all()


@app.post("/api/v1/orders", status_code=201)
def create_order(payload: OrderInput, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    ordered_at = ensure_aware(payload.ordered_at)
    linked_visit = None
    if payload.visit_id:
        linked_visit = db.get(Visit, payload.visit_id)
        if not linked_visit or linked_visit.customer_id != customer.id:
            raise HTTPException(status_code=422, detail="Lần mua sắm không thuộc khách hàng")
        allowance = timedelta(seconds=get_settings().visit_idle_timeout_seconds)
        end_time = linked_visit.ended_at or linked_visit.last_seen_at
        if ordered_at < ensure_aware(linked_visit.started_at) or ordered_at > ensure_aware(end_time) + allowance:
            raise HTTPException(status_code=422, detail="Thời gian đơn hàng nằm ngoài lần mua sắm đã chọn")
    else:
        linked_visit = find_visit_for_order(db, customer.id, ordered_at)
    order = Order(
        external_code=payload.external_code,
        customer_id=customer.id,
        visit_id=linked_visit.id if linked_visit else None,
        ordered_at=ordered_at,
        status=payload.status,
        demo_data=payload.demo_data,
    )
    db.add(order)
    create_order_items(db, order, [item.model_dump() for item in payload.items])
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Mã đơn hàng đã tồn tại") from exc
    db.refresh(order)
    return db.scalar(select(Order).options(selectinload(Order.items)).where(Order.id == order.id))


@app.get("/api/v1/orders/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    order = db.scalar(select(Order).options(selectinload(Order.items), selectinload(Order.customer)).where(Order.id == order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    return order


@app.patch("/api/v1/orders/{order_id}")
def update_order_status(payload: OrderStatusInput, order_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order


@app.post("/api/v1/observations", status_code=201)
async def create_observation(
    event_id: str | None = Form(None),
    touchpoint_id: str | None = Form(None),
    observed_at: str | None = Form(None),
    experiment_run_id: str | None = Form(None),
    demo_data: bool = Form(False),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    vision: VisionClient = Depends(get_vision_client),
):
    event_id = event_id.strip() if event_id else None
    experiment_run_id = experiment_run_id.strip() if experiment_run_id else None
    if experiment_run_id and len(experiment_run_id) > 64:
        raise HTTPException(status_code=422, detail="experiment_run_id vượt quá 64 ký tự")
    if experiment_run_id and not demo_data:
        raise HTTPException(status_code=422, detail="experiment_run_id chỉ dùng cho dữ liệu demo/nghiên cứu")
    if not event_id:
        record_ingestion_issue(db, event_id=None, touchpoint_reference=touchpoint_id, observed_at_text=observed_at, issue_code="MISSING_EVENT_ID", detail="Thiếu mã sự kiện")
        raise HTTPException(status_code=422, detail="Thiếu mã sự kiện")
    existing = db.scalar(
        select(CaptureEvent)
        .options(selectinload(CaptureEvent.observations))
        .where(CaptureEvent.event_id == event_id)
    )
    if existing:
        return {
            "capture_event_id": existing.id,
            "event_id": existing.event_id,
            "image_status": existing.image_status,
            "face_count": existing.face_count,
            "observations": existing.observations,
        }
    if not touchpoint_id:
        record_ingestion_issue(db, event_id=event_id, touchpoint_reference=None, observed_at_text=observed_at, issue_code="MISSING_TOUCHPOINT", detail="Thiếu mã khu vực")
        raise HTTPException(status_code=422, detail="Thiếu mã khu vực")
    touchpoint = db.get(Touchpoint, touchpoint_id)
    if not touchpoint or not touchpoint.active:
        record_ingestion_issue(db, event_id=event_id, touchpoint_reference=touchpoint_id, observed_at_text=observed_at, issue_code="INVALID_TOUCHPOINT", detail="Khu vực không tồn tại hoặc đã ngừng hoạt động")
        raise HTTPException(status_code=422, detail="Khu vực không tồn tại hoặc đã ngừng hoạt động")
    try:
        parsed_observed_at = parse_observed_at(observed_at)
    except ValueError as exc:
        record_ingestion_issue(db, event_id=event_id, touchpoint_reference=touchpoint_id, observed_at_text=observed_at, issue_code="INVALID_OBSERVED_AT", detail=str(exc))
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if image is None:
        record_ingestion_issue(db, event_id=event_id, touchpoint_reference=touchpoint_id, observed_at_text=observed_at, issue_code="MISSING_IMAGE", detail="Thiếu dữ liệu ảnh")
        raise HTTPException(status_code=422, detail="Thiếu dữ liệu ảnh")
    image_bytes = await read_image(image)
    try:
        result = await vision.analyze(image_bytes, image.filename or "image.jpg", image.content_type)
    except Exception as exc:
        capture = CaptureEvent(
            event_id=event_id,
            touchpoint_id=touchpoint.id,
            observed_at=parsed_observed_at,
            image_status="MODEL_ERROR",
            face_count=0,
            experiment_run_id=experiment_run_id,
            demo_data=demo_data,
        )
        db.add(capture)
        audit(db, user, "CAPTURE_EVENT_FAILED", "capture_event", capture.id, {"event_id": event_id})
        db.commit()
        raise HTTPException(status_code=502, detail="Dịch vụ xử lý ảnh không phản hồi") from exc

    capture = CaptureEvent(
        event_id=event_id,
        touchpoint_id=touchpoint.id,
        observed_at=parsed_observed_at,
        image_status=result.image_status,
        face_count=result.face_count,
        detector_version=result.models.get("detector"),
        experiment_run_id=experiment_run_id,
        demo_data=demo_data,
    )
    db.add(capture)
    db.flush()
    observations = []
    for face in result.faces:
        customer = None
        distance = None
        identity_status = face.identity_status
        visit = None
        if face.image_status == "VALID" and face.identity_status == "VALID" and face.embedding:
            customer, distance, identity_status = match_customer(db, face.embedding)
            if customer:
                visit = get_or_create_visit(db, customer, parsed_observed_at, demo_data)
        if not customer or not visit:
            continue
        observation = Observation(
            capture_event_id=capture.id,
            event_id=event_id,
            face_index=face.face_index,
            touchpoint_id=touchpoint.id,
            observed_at=parsed_observed_at,
            customer_id=customer.id,
            visit_id=visit.id,
            expression_label=face.expression_label,
            expression_confidence=face.expression_confidence,
            expression_scores=face.expression_scores,
            face_match_distance=distance,
            bounding_box=face.box,
            detection_score=face.detection_score,
            image_status=face.image_status,
            expression_status=face.expression_status,
            identity_status=identity_status,
            detector_version=result.models.get("detector"),
            emotion_model_version=result.models.get("emotion"),
            recognition_model_version=result.models.get("embedding"),
            experiment_run_id=experiment_run_id,
            demo_data=demo_data,
        )
        db.add(observation)
        observations.append(observation)
    audit(
        db,
        user,
        "CAPTURE_EVENT_CREATED",
        "capture_event",
        capture.id,
        {"event_id": event_id, "face_count": result.face_count, "saved_observation_count": len(observations)},
    )
    db.commit()
    for observation in observations:
        db.refresh(observation)
    return {
        "capture_event_id": capture.id,
        "event_id": capture.event_id,
        "image_status": capture.image_status,
        "face_count": capture.face_count,
        "observations": observations,
    }


@app.post("/api/v1/simulation/observations/batch", status_code=201)
def create_simulated_observations(
    payload: SimulatedObservationBatchInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN)),
):
    created = []
    skipped = 0
    for item in payload.observations:
        existing_capture = db.scalar(
            select(CaptureEvent)
            .options(selectinload(CaptureEvent.observations))
            .where(CaptureEvent.event_id == item.event_id)
        )
        if existing_capture:
            skipped += 1
            existing = existing_capture.observations[0] if existing_capture.observations else None
            created.append(
                {
                    "event_id": existing_capture.event_id,
                    "observation_id": existing.id if existing else None,
                    "visit_id": existing.visit_id if existing else None,
                }
            )
            continue
        touchpoint = db.get(Touchpoint, item.touchpoint_id)
        if not touchpoint or not touchpoint.active:
            raise HTTPException(status_code=422, detail=f"Điểm chạm không hợp lệ: {item.touchpoint_id}")
        customer = db.get(Customer, item.customer_id) if item.customer_id else None
        if item.customer_id and not customer:
            raise HTTPException(status_code=422, detail=f"Khách hàng không tồn tại: {item.customer_id}")
        if item.expression_label and item.expression_label not in EXPRESSION_LABELS:
            raise HTTPException(status_code=422, detail=f"Nhãn biểu cảm không hợp lệ: {item.expression_label}")
        observed_at = ensure_aware(item.observed_at)
        capture = CaptureEvent(
            event_id=item.event_id,
            touchpoint_id=touchpoint.id,
            observed_at=observed_at,
            image_status=item.image_status,
            face_count=1 if item.image_status == "VALID" else 0,
            detector_version="simulator",
            source_type="SIMULATOR",
            simulation_run_id=item.simulation_run_id,
            demo_data=True,
        )
        db.add(capture)
        db.flush()
        if item.image_status != "VALID" or not customer:
            created.append({"event_id": item.event_id, "observation_id": None, "visit_id": None})
            continue
        visit = get_or_create_visit(db, customer, observed_at, True)
        observation = Observation(
            capture_event_id=capture.id,
            event_id=item.event_id,
            face_index=0,
            touchpoint_id=touchpoint.id,
            observed_at=observed_at,
            customer_id=customer.id,
            visit_id=visit.id,
            expression_label=item.expression_label,
            expression_confidence=item.expression_confidence,
            expression_scores=None,
            image_status=item.image_status,
            expression_status=item.expression_status,
            identity_status=item.identity_status,
            detector_version="simulator",
            emotion_model_version="simulator",
            recognition_model_version="simulator",
            source_type="SIMULATOR",
            simulation_run_id=item.simulation_run_id,
            demo_data=True,
        )
        db.add(observation)
        db.flush()
        if visit and item.end_of_visit:
            visit.status = VisitStatus.CLOSED
            visit.ended_at = observed_at
            visit.last_seen_at = observed_at
            visit.close_reason = "SIMULATED_END"
            # Ghi trạng thái đóng trước khi tạo lượt tiếp theo của cùng khách hàng.
            # PostgreSQL dùng chỉ mục duy nhất cho lượt ACTIVE nên thứ tự ghi là bắt buộc.
            db.flush()
        created.append({"event_id": observation.event_id, "observation_id": observation.id, "visit_id": observation.visit_id})
    audit(
        db,
        user,
        "SIMULATION_BATCH_INGESTED",
        "simulation_run",
        None,
        {"created": len(created) - skipped, "skipped": skipped, "run_ids": sorted({item.simulation_run_id for item in payload.observations})},
    )
    db.commit()
    return {"items": created, "created": len(created) - skipped, "skipped": skipped}


@app.get("/api/v1/observations")
def list_observations(
    touchpoint_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    stmt = select(Observation).options(selectinload(Observation.touchpoint), selectinload(Observation.customer))
    count_stmt = select(func.count()).select_from(Observation)
    conditions = [Observation.customer_id.is_not(None)]
    if touchpoint_id:
        conditions.append(Observation.touchpoint_id == touchpoint_id)
    if conditions:
        stmt = stmt.where(*conditions)
        count_stmt = count_stmt.where(*conditions)
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.order_by(Observation.observed_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": rows, "page": page, "page_size": page_size, "total": total}


@app.get("/api/v1/visits")
def list_visits(
    customer_id: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    stmt = select(Visit).options(selectinload(Visit.customer)).order_by(Visit.started_at.desc())
    if customer_id:
        stmt = stmt.where(Visit.customer_id == customer_id)
    return db.scalars(stmt).all()


@app.get("/api/v1/visits/{visit_id}")
def get_visit(visit_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    visit = db.get(Visit, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Không tìm thấy lượt ghé thăm")
    observations = db.scalars(
        select(Observation)
        .options(selectinload(Observation.touchpoint))
        .where(Observation.visit_id == visit_id)
        .order_by(Observation.observed_at, Observation.id)
    ).all()
    orders = db.scalars(select(Order).options(selectinload(Order.items)).where(Order.visit_id == visit_id).order_by(Order.ordered_at)).all()
    return {"visit": visit, "observations": observations, "orders": orders}


@app.post("/api/v1/visits/{visit_id}/close")
def close_visit(visit_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    visit = db.get(Visit, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Không tìm thấy lượt ghé thăm")
    visit.status = VisitStatus.CLOSED
    visit.ended_at = visit.last_seen_at
    visit.close_reason = "MANUAL"
    audit(db, user, "VISIT_CLOSED", "visit", visit.id)
    db.commit()
    return visit


@app.get("/api/v1/visits/{visit_id}/analysis")
def visit_analysis(visit_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    visit = db.get(Visit, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Không tìm thấy lần mua sắm")
    observations = db.scalars(
        select(Observation)
        .options(selectinload(Observation.touchpoint))
        .where(Observation.visit_id == visit_id)
        .order_by(Observation.observed_at, Observation.id)
    ).all()
    conflict_ids: set[str] = set()
    by_time: dict[datetime, list[Observation]] = {}
    for item in observations:
        by_time.setdefault(item.observed_at, []).append(item)
    for same_time in by_time.values():
        if len({item.touchpoint_id for item in same_time}) > 1:
            conflict_ids.update(item.id for item in same_time)

    valid_orders = sorted({item.touchpoint.sequence_order for item in observations if item.touchpoint})
    missing = []
    if valid_orders:
        present_ids = {item.touchpoint_id for item in observations}
        missing = db.scalars(
            select(Touchpoint)
            .where(
                Touchpoint.active.is_(True),
                Touchpoint.sequence_order >= valid_orders[0],
                Touchpoint.sequence_order <= valid_orders[-1],
                Touchpoint.id.not_in(present_ids),
            )
            .order_by(Touchpoint.sequence_order)
        ).all()

    late_limit = timedelta(seconds=get_settings().late_event_tolerance_seconds)
    rows = []
    late_count = 0
    for item in observations:
        observed = item.observed_at.replace(tzinfo=timezone.utc) if item.observed_at.tzinfo is None else item.observed_at.astimezone(timezone.utc)
        received = item.received_at.replace(tzinfo=timezone.utc) if item.received_at.tzinfo is None else item.received_at.astimezone(timezone.utc)
        late = received - observed > late_limit
        late_count += int(late)
        flags = []
        if item.id in conflict_ids:
            flags.extend(["TIME_CONFLICT", "IDENTITY_CONFLICT"])
        if late:
            flags.append("LATE_ARRIVAL")
        rows.append({"observation_id": item.id, "flags": flags, "eligible_for_change_analysis": item.id not in conflict_ids})
    return {
        "visit_id": visit_id,
        "observation_flags": rows,
        "missing_touchpoints": [to_dict(item, "id", "touchpoint_code", "name", "sequence_order") for item in missing],
        "summary": {
            "observations": len(observations),
            "missing_touchpoints": len(missing),
            "time_conflicts": len(conflict_ids),
            "late_arrivals": late_count,
        },
    }


def sequence_run_payload(run: SequenceAnalysisRun) -> dict:
    return {
        "id": run.id,
        "source_type": run.source_type,
        "source_run_id": run.source_run_id,
        "status": run.status,
        "preprocessing_version": run.preprocessing_version,
        "algorithm_version": run.algorithm_version,
        "parameters": run.parameters,
        "candidate_metrics": run.candidate_metrics,
        "warnings": run.warnings,
        "received_visit_count": run.received_visit_count,
        "used_visit_count": run.used_visit_count,
        "excluded_visit_count": run.excluded_visit_count,
        "selected_k": run.selected_k,
        "average_silhouette_width": run.average_silhouette_width,
        "distance_matrix_sha256": run.distance_matrix_sha256,
        "error_detail": run.error_detail,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
    }


def sequence_cluster_payload(cluster: SequenceClusterSummary) -> dict:
    return {
        "id": cluster.id,
        "run_id": cluster.run_id,
        "cluster_id": cluster.cluster_id,
        "medoid_visit_id": cluster.medoid_visit_id,
        "medoid_sequence": cluster.medoid_sequence,
        "size": cluster.size,
        "proportion": cluster.proportion,
        "mean_silhouette": cluster.mean_silhouette,
        "median_distance": cluster.median_distance,
        "display_name": cluster.display_name,
    }


def sequence_assignment_payload(assignment: SequenceClusterAssignment) -> dict:
    visit = assignment.visit
    customer = visit.customer if visit else None
    return {
        "id": assignment.id,
        "run_id": assignment.run_id,
        "visit_id": assignment.visit_id,
        "cluster_id": assignment.cluster_id,
        "sequence": assignment.sequence,
        "sequence_metadata": assignment.sequence_metadata,
        "distance_to_medoid": assignment.distance_to_medoid,
        "silhouette": assignment.silhouette,
        "visit_started_at": visit.started_at if visit else None,
        "customer": (
            {"id": customer.id, "customer_code": customer.customer_code, "full_name": customer.full_name}
            if customer
            else None
        ),
    }


@app.post("/api/v1/sequence-analyses", status_code=201)
def create_sequence_analysis(
    payload: SequenceAnalysisInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN)),
):
    config = AnalysisConfig(
        min_states=payload.min_states,
        min_cluster_size_abs=payload.min_cluster_size_abs,
        min_cluster_ratio=payload.min_cluster_ratio,
        k_min=payload.k_min,
        k_max=payload.k_max,
        asw_tolerance=payload.asw_tolerance,
        random_state=payload.random_state,
    )
    try:
        config.validate()
    except SequenceAnalysisError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    parameters = payload.model_dump()
    run = SequenceAnalysisRun(
        source_type=payload.source_type,
        source_run_id=payload.source_run_id,
        status="RUNNING",
        preprocessing_version=PREPROCESSING_VERSION,
        algorithm_version=ALGORITHM_VERSION,
        parameters=parameters,
        candidate_metrics=[],
        warnings=[],
        created_by=user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        conditions = [
            Observation.source_type == payload.source_type,
            Observation.image_status == "VALID",
            Observation.expression_status == "VALID",
            Observation.visit_id.is_not(None),
            Observation.expression_label.in_(EXPRESSION_LABELS),
        ]
        if payload.source_type == "SIMULATOR":
            conditions.append(Observation.simulation_run_id == payload.source_run_id)
        else:
            conditions.append(Observation.experiment_run_id == payload.source_run_id)
        observations = db.scalars(
            select(Observation)
            .options(selectinload(Observation.touchpoint))
            .where(*conditions)
            .order_by(Observation.visit_id, Observation.observed_at, Observation.id)
        ).all()
        sequence_rows = [
            SequenceObservation(
                observation_id=item.id,
                visit_id=item.visit_id,
                touchpoint_id=item.touchpoint_id,
                touchpoint_name=item.touchpoint.name if item.touchpoint else item.touchpoint_id,
                observed_at=item.observed_at,
                expression_label=item.expression_label,
                expression_confidence=item.expression_confidence,
            )
            for item in observations
        ]
        prepared = prepare_visit_sequences(sequence_rows, min_states=config.min_states)
        clustered = cluster_visit_sequences(prepared.sequences, config)

        for item in clustered.clusters:
            db.add(SequenceClusterSummary(run_id=run.id, **item))
        for item in clustered.assignments:
            db.add(SequenceClusterAssignment(run_id=run.id, **item))
        run.status = "COMPLETED"
        run.received_visit_count = prepared.received_visit_count
        run.used_visit_count = len(prepared.sequences)
        run.excluded_visit_count = len(prepared.excluded)
        run.selected_k = clustered.selected_k
        run.average_silhouette_width = clustered.average_silhouette_width
        run.distance_matrix_sha256 = hashlib.sha256(
            clustered.distance_matrix.astype("<f8", copy=False).tobytes(order="C")
        ).hexdigest()
        run.candidate_metrics = clustered.candidate_metrics
        run.warnings = [*prepared.warnings, *clustered.warnings]
        run.parameters = {**parameters, "excluded_visits": prepared.excluded}
        run.completed_at = datetime.now(timezone.utc)
        audit(
            db,
            user,
            "SEQUENCE_ANALYSIS_COMPLETED",
            "sequence_analysis_run",
            run.id,
            {"selected_k": run.selected_k, "used_visit_count": run.used_visit_count},
        )
        db.commit()
        db.refresh(run)
        return sequence_run_payload(run)
    except SequenceAnalysisError as exc:
        db.rollback()
        failed = db.get(SequenceAnalysisRun, run.id)
        failed.status = "FAILED"
        failed.error_detail = str(exc)
        failed.completed_at = datetime.now(timezone.utc)
        audit(db, user, "SEQUENCE_ANALYSIS_FAILED", "sequence_analysis_run", failed.id, {"detail": str(exc)})
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        failed = db.get(SequenceAnalysisRun, run.id)
        failed.status = "FAILED"
        failed.error_detail = f"{type(exc).__name__}: {exc}"[:1024]
        failed.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=500, detail="Không thể hoàn thành phân tích chuỗi") from exc


@app.get("/api/v1/sequence-analyses")
def list_sequence_analyses(
    source_type: str | None = Query(default=None, pattern="^(CAMERA|SIMULATOR)$"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    stmt = select(SequenceAnalysisRun).order_by(SequenceAnalysisRun.created_at.desc())
    if source_type:
        stmt = stmt.where(SequenceAnalysisRun.source_type == source_type)
    return [sequence_run_payload(item) for item in db.scalars(stmt).all()]


@app.get("/api/v1/sequence-analyses/{run_id}")
def get_sequence_analysis(run_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    run = db.get(SequenceAnalysisRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Không tìm thấy lần phân tích chuỗi")
    return sequence_run_payload(run)


@app.get("/api/v1/sequence-analyses/{run_id}/clusters")
def list_sequence_clusters(run_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    if not db.get(SequenceAnalysisRun, run_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy lần phân tích chuỗi")
    rows = db.scalars(
        select(SequenceClusterSummary)
        .where(SequenceClusterSummary.run_id == run_id)
        .order_by(SequenceClusterSummary.cluster_id)
    ).all()
    return [sequence_cluster_payload(item) for item in rows]


@app.patch("/api/v1/sequence-analyses/{run_id}/clusters/{cluster_id}")
def patch_sequence_cluster(
    payload: SequenceClusterPatch,
    run_id: str,
    cluster_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN)),
):
    cluster = db.scalar(
        select(SequenceClusterSummary).where(
            SequenceClusterSummary.run_id == run_id,
            SequenceClusterSummary.cluster_id == cluster_id,
        )
    )
    if not cluster:
        raise HTTPException(status_code=404, detail="Không tìm thấy cụm")
    cluster.display_name = payload.display_name.strip() if payload.display_name else None
    audit(db, user, "SEQUENCE_CLUSTER_RENAMED", "sequence_cluster", cluster.id, {"display_name": cluster.display_name})
    db.commit()
    db.refresh(cluster)
    return sequence_cluster_payload(cluster)


@app.get("/api/v1/sequence-analyses/{run_id}/assignments")
def list_sequence_assignments(
    run_id: str,
    cluster_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    if not db.get(SequenceAnalysisRun, run_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy lần phân tích chuỗi")
    conditions = [SequenceClusterAssignment.run_id == run_id]
    if cluster_id is not None:
        conditions.append(SequenceClusterAssignment.cluster_id == cluster_id)
    total = db.scalar(select(func.count()).select_from(SequenceClusterAssignment).where(*conditions)) or 0
    rows = db.scalars(
        select(SequenceClusterAssignment)
        .options(selectinload(SequenceClusterAssignment.visit).selectinload(Visit.customer))
        .where(*conditions)
        .order_by(SequenceClusterAssignment.cluster_id, SequenceClusterAssignment.silhouette.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [sequence_assignment_payload(item) for item in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@app.get("/api/v1/observations/{observation_id}/revisions")
def list_observation_revisions(observation_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    if not db.get(Observation, observation_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi quan sát")
    return db.scalars(
        select(ObservationRevision)
        .where(ObservationRevision.observation_id == observation_id)
        .order_by(ObservationRevision.revision_number.desc())
    ).all()


@app.post("/api/v1/observations/{observation_id}/reprocess")
async def reprocess_observation(
    observation_id: str,
    image: UploadFile = File(...),
    reason: str = Form("MANUAL_REPROCESS"),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN)),
    vision: VisionClient = Depends(get_vision_client),
):
    observation = db.get(Observation, observation_id)
    if not observation:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi quan sát")
    result = await vision.analyze(await read_image(image), image.filename or "image.jpg", image.content_type)
    face = result.single_face()
    if result.image_status != "VALID" or not face:
        status = "MULTIPLE_FACES" if result.face_count > 1 else result.image_status
        raise HTTPException(status_code=422, detail=f"Ảnh xử lý lại phải chứa đúng một khuôn mặt hợp lệ: {status}")
    customer = None
    distance = None
    identity_status = face.identity_status
    visit = None
    if face.image_status == "VALID" and face.identity_status == "VALID" and face.embedding:
        customer, distance, identity_status = match_customer(db, face.embedding)
        if customer:
            observed_at = observation.observed_at.replace(tzinfo=timezone.utc) if observation.observed_at.tzinfo is None else observation.observed_at.astimezone(timezone.utc)
            visit = attach_visit(db, customer, observed_at, observation.demo_data)
    if not customer or not visit:
        raise HTTPException(status_code=422, detail="Ảnh không khớp với khách hàng đã đăng ký")
    save_observation_revision(db, observation, reason[:64], user)
    observation.customer_id = customer.id
    observation.visit_id = visit.id
    observation.expression_label = face.expression_label
    observation.expression_confidence = face.expression_confidence
    observation.expression_scores = face.expression_scores
    observation.face_match_distance = distance
    observation.bounding_box = face.box
    observation.detection_score = face.detection_score
    observation.image_status = face.image_status
    observation.expression_status = face.expression_status
    observation.identity_status = identity_status
    observation.detector_version = result.models.get("detector")
    observation.emotion_model_version = result.models.get("emotion")
    observation.recognition_model_version = result.models.get("embedding")
    audit(db, user, "OBSERVATION_REPROCESSED", "observation", observation.id, {"reason": reason[:64]})
    db.commit()
    db.refresh(observation)
    return observation


@app.get("/api/v1/reports/expression-distribution")
def expression_distribution(
    touchpoint_id: str | None = None,
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    stmt = (
        select(Touchpoint.id, Touchpoint.name, Observation.expression_label, func.count(Observation.id))
        .join(Observation, Observation.touchpoint_id == Touchpoint.id)
        .where(
            Observation.customer_id.is_not(None),
            Observation.image_status == "VALID",
            Observation.expression_status == "VALID",
        )
        .group_by(Touchpoint.id, Touchpoint.name, Observation.expression_label)
        .order_by(Touchpoint.sequence_order, Observation.expression_label)
    )
    if touchpoint_id:
        stmt = stmt.where(Touchpoint.id == touchpoint_id)
    if from_time:
        stmt = stmt.where(Observation.observed_at >= ensure_aware(from_time))
    if to_time:
        stmt = stmt.where(Observation.observed_at <= ensure_aware(to_time))
    rows = db.execute(stmt).all()
    totals: dict[str, int] = {}
    for touchpoint, _name, _label, count in rows:
        totals[touchpoint] = totals.get(touchpoint, 0) + count
    return [
        {
            "touchpoint_id": touchpoint,
            "touchpoint_name": name,
            "label": label,
            "count": count,
            "percentage": count / totals[touchpoint] if totals[touchpoint] else None,
        }
        for touchpoint, name, label, count in rows
    ]


@app.get("/api/v1/reports/expression-timeline")
def expression_timeline(
    touchpoint_id: str,
    bucket_minutes: int = Query(15, ge=5, le=120),
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    touchpoint = db.get(Touchpoint, touchpoint_id)
    if not touchpoint:
        raise HTTPException(status_code=404, detail="Không tìm thấy điểm chạm")

    stmt = (
        select(Observation.observed_at, Observation.expression_label)
        .where(
            Observation.customer_id.is_not(None),
            Observation.touchpoint_id == touchpoint_id,
            Observation.image_status == "VALID",
            Observation.expression_status == "VALID",
            Observation.expression_label.is_not(None),
        )
        .order_by(Observation.observed_at, Observation.id)
    )
    if from_time:
        stmt = stmt.where(Observation.observed_at >= ensure_aware(from_time))
    if to_time:
        stmt = stmt.where(Observation.observed_at <= ensure_aware(to_time))

    bucket_seconds = bucket_minutes * 60
    counts: dict[tuple[datetime, str], int] = {}
    for observed_at, label in db.execute(stmt).all():
        # SQLite trong bộ kiểm thử không giữ thông tin múi giờ.
        # Thời gian quan sát được lưu theo UTC nên chỉ khôi phục UTC cho dữ liệu đọc từ cơ sở dữ liệu.
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        else:
            observed_at = observed_at.astimezone(timezone.utc)
        bucket_epoch = int(observed_at.timestamp()) // bucket_seconds * bucket_seconds
        bucket_start = datetime.fromtimestamp(bucket_epoch, tz=timezone.utc)
        key = (bucket_start, label)
        counts[key] = counts.get(key, 0) + 1

    return [
        {
            "touchpoint_id": touchpoint.id,
            "touchpoint_name": touchpoint.name,
            "bucket_start": bucket_start,
            "bucket_minutes": bucket_minutes,
            "label": label,
            "count": count,
        }
        for (bucket_start, label), count in sorted(counts.items())
    ]


@app.get("/api/v1/reports/data-quality")
def data_quality(
    touchpoint_id: str | None = None,
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    observation_conditions = [Observation.customer_id.is_not(None)]
    capture_conditions = []
    if touchpoint_id:
        observation_conditions.append(Observation.touchpoint_id == touchpoint_id)
        capture_conditions.append(CaptureEvent.touchpoint_id == touchpoint_id)
    if from_time:
        start = ensure_aware(from_time)
        observation_conditions.append(Observation.observed_at >= start)
        capture_conditions.append(CaptureEvent.observed_at >= start)
    if to_time:
        end = ensure_aware(to_time)
        observation_conditions.append(Observation.observed_at <= end)
        capture_conditions.append(CaptureEvent.observed_at <= end)
    return quality_status_rows(db, observation_conditions, capture_conditions)


def quality_status_rows(db: Session, observation_conditions: list, capture_conditions: list) -> list[dict]:
    counts: dict[tuple[str, str, str], int] = {}
    observation_stmt = select(
        Observation.image_status,
        Observation.expression_status,
        Observation.identity_status,
        func.count(Observation.id),
    )
    if observation_conditions:
        observation_stmt = observation_stmt.where(*observation_conditions)
    for image, expression, identity, count in db.execute(
        observation_stmt.group_by(Observation.image_status, Observation.expression_status, Observation.identity_status)
    ).all():
        counts[(image, expression, identity)] = count

    capture_stmt = select(CaptureEvent.image_status, func.count(CaptureEvent.id)).where(CaptureEvent.face_count == 0)
    if capture_conditions:
        capture_stmt = capture_stmt.where(*capture_conditions)
    for image, count in db.execute(capture_stmt.group_by(CaptureEvent.image_status)).all():
        key = (image, "NOT_RUN", "NOT_RUN")
        counts[key] = counts.get(key, 0) + count

    return [
        {"image_status": key[0], "expression_status": key[1], "identity_status": key[2], "count": count}
        for key, count in sorted(counts.items())
    ]


@app.get("/api/v1/reports/data-quality-summary")
def data_quality_summary(
    touchpoint_id: str | None = None,
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    conditions = [Observation.customer_id.is_not(None)]
    capture_conditions = []
    issue_conditions = []
    if touchpoint_id:
        conditions.append(Observation.touchpoint_id == touchpoint_id)
        capture_conditions.append(CaptureEvent.touchpoint_id == touchpoint_id)
        issue_conditions.append(IngestionIssue.touchpoint_reference == touchpoint_id)
    if from_time:
        start = ensure_aware(from_time)
        conditions.append(Observation.observed_at >= start)
        capture_conditions.append(CaptureEvent.observed_at >= start)
        issue_conditions.append(IngestionIssue.received_at >= start)
    if to_time:
        end = ensure_aware(to_time)
        conditions.append(Observation.observed_at <= end)
        capture_conditions.append(CaptureEvent.observed_at <= end)
        issue_conditions.append(IngestionIssue.received_at <= end)

    statuses = quality_status_rows(db, conditions, capture_conditions)
    issue_stmt = select(IngestionIssue.issue_code, func.count(IngestionIssue.id))
    if issue_conditions:
        issue_stmt = issue_stmt.where(*issue_conditions)
    issues = [{"issue_code": code, "count": count} for code, count in db.execute(issue_stmt.group_by(IngestionIssue.issue_code)).all()]

    observation_stmt = select(Observation)
    if conditions:
        observation_stmt = observation_stmt.where(*conditions)
    observations = db.scalars(observation_stmt).all()
    capture_stmt = select(CaptureEvent)
    if capture_conditions:
        capture_stmt = capture_stmt.where(*capture_conditions)
    captures = db.scalars(capture_stmt).all()
    late_limit = timedelta(seconds=get_settings().late_event_tolerance_seconds)
    late_count = sum(
        int(
            (item.received_at.replace(tzinfo=timezone.utc) if item.received_at.tzinfo is None else item.received_at.astimezone(timezone.utc))
            - (item.observed_at.replace(tzinfo=timezone.utc) if item.observed_at.tzinfo is None else item.observed_at.astimezone(timezone.utc))
            > late_limit
        )
        for item in captures
    )
    by_visit_time: dict[tuple[str, datetime], set[str]] = {}
    for item in observations:
        if item.visit_id:
            by_visit_time.setdefault((item.visit_id, item.observed_at), set()).add(item.touchpoint_id)
    time_conflicts = sum(len(points) for points in by_visit_time.values() if len(points) > 1)

    visits_stmt = select(Visit.id)
    if from_time:
        visits_stmt = visits_stmt.where(Visit.started_at >= ensure_aware(from_time))
    if to_time:
        visits_stmt = visits_stmt.where(Visit.started_at <= ensure_aware(to_time))
    visit_ids = db.scalars(visits_stmt).all()
    missing_total = 0
    eligible_visits = 0
    for visit_id in visit_ids:
        visit_observations = [item for item in observations if item.visit_id == visit_id]
        if not visit_observations:
            continue
        eligible_visits += int(len(visit_observations) >= 2 and not any(len(points) > 1 for (candidate, _), points in by_visit_time.items() if candidate == visit_id))
        orders = sorted({item.touchpoint.sequence_order for item in db.scalars(select(Observation).options(selectinload(Observation.touchpoint)).where(Observation.visit_id == visit_id)).all() if item.touchpoint})
        if orders:
            present = {item.touchpoint_id for item in db.scalars(select(Observation).where(Observation.visit_id == visit_id)).all()}
            missing_total += db.scalar(select(func.count()).select_from(Touchpoint).where(Touchpoint.active.is_(True), Touchpoint.sequence_order >= orders[0], Touchpoint.sequence_order <= orders[-1], Touchpoint.id.not_in(present))) or 0
    return {
        "statuses": statuses,
        "ingestion_issues": issues,
        "summary": {
            "capture_events": len(captures),
            "observations": len(observations),
            "late_arrivals": late_count,
            "time_conflicts": time_conflicts,
            "missing_touchpoints": missing_total,
            "eligible_visits": eligible_visits,
        },
    }


@app.get("/api/v1/reports/expression-changes")
def expression_changes(
    from_touchpoint_id: str | None = None,
    to_touchpoint_id: str | None = None,
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
    representative: str = Query("highest_confidence", pattern="^(first|last|highest_confidence)$"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    stmt = (
        select(Observation)
        .where(
            Observation.visit_id.is_not(None),
            Observation.image_status == "VALID",
            Observation.expression_status == "VALID",
        )
        .order_by(Observation.visit_id, Observation.observed_at, Observation.id)
    )
    if from_time:
        stmt = stmt.where(Observation.observed_at >= ensure_aware(from_time))
    if to_time:
        stmt = stmt.where(Observation.observed_at <= ensure_aware(to_time))
    rows = db.scalars(stmt).all()
    by_visit: dict[str, list[Observation]] = {}
    for row in rows:
        by_visit.setdefault(row.visit_id, []).append(row)
    counts: dict[tuple[str, str, str, str], int] = {}
    for observations in by_visit.values():
        observations.sort(key=lambda item: (item.observed_at, item.id))
        conflict_ids: set[str] = set()
        at_time: dict[datetime, list[Observation]] = {}
        for item in observations:
            at_time.setdefault(item.observed_at, []).append(item)
        for items in at_time.values():
            if len({item.touchpoint_id for item in items}) > 1:
                conflict_ids.update(item.id for item in items)
        clean = [item for item in observations if item.id not in conflict_ids]
        groups: list[list[Observation]] = []
        for item in clean:
            if not groups or groups[-1][-1].touchpoint_id != item.touchpoint_id:
                groups.append([item])
            else:
                groups[-1].append(item)
        representatives = []
        for group in groups:
            if representative == "first":
                representatives.append(group[0])
            elif representative == "last":
                representatives.append(group[-1])
            else:
                representatives.append(max(group, key=lambda item: item.expression_confidence or 0.0))
        for before, after in zip(representatives, representatives[1:]):
            if from_touchpoint_id and before.touchpoint_id != from_touchpoint_id:
                continue
            if to_touchpoint_id and after.touchpoint_id != to_touchpoint_id:
                continue
            key = (before.touchpoint_id, after.touchpoint_id, before.expression_label, after.expression_label)
            counts[key] = counts.get(key, 0) + 1
    pair_totals: dict[tuple[str, str], int] = {}
    for key, count in counts.items():
        pair_totals[(key[0], key[1])] = pair_totals.get((key[0], key[1]), 0) + count
    return [
        {
            "from_touchpoint_id": key[0],
            "to_touchpoint_id": key[1],
            "from_label": key[2],
            "to_label": key[3],
            "count": count,
            "percentage": count / pair_totals[(key[0], key[1])],
            "representative": representative,
        }
        for key, count in sorted(counts.items())
    ]
