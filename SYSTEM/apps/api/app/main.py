from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .config import get_settings
from .database import Base, SessionLocal, engine, get_db
from .logic import create_order_items, ensure_aware, get_or_create_visit, load_face_threshold, match_customer
from .models import (
    AuditLog,
    Customer,
    FaceTemplate,
    Observation,
    Order,
    OrderStatus,
    Product,
    ProductCategory,
    RecordStatus,
    Role,
    Touchpoint,
    User,
    Visit,
    VisitStatus,
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
    if result.image_status != "VALID" or not result.embedding:
        raise HTTPException(status_code=422, detail=f"Không thể tạo mẫu khuôn mặt: {result.image_status}")
    template = FaceTemplate(
        customer_id=customer.id,
        embedding=result.embedding,
        model_name="ArcFace",
        model_version=result.models.get("embedding", "unknown"),
        quality_score=result.detection_score,
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
    if result.image_status != "VALID" or not result.embedding:
        return {"status": result.image_status, "customer": None}
    customer, distance, identity_status = match_customer(db, result.embedding)
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
    active_visit = None
    if payload.visit_id:
        active_visit = db.get(Visit, payload.visit_id)
        if not active_visit or active_visit.customer_id != customer.id:
            raise HTTPException(status_code=422, detail="Lượt ghé thăm không thuộc khách hàng")
    else:
        active_visit = db.scalar(select(Visit).where(Visit.customer_id == customer.id, Visit.status == VisitStatus.ACTIVE))
    order = Order(
        external_code=payload.external_code,
        customer_id=customer.id,
        visit_id=active_visit.id if active_visit else None,
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
    event_id: str = Form(...),
    touchpoint_id: str = Form(...),
    observed_at: datetime = Form(...),
    demo_data: bool = Form(False),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    vision: VisionClient = Depends(get_vision_client),
):
    existing = db.scalar(select(Observation).where(Observation.event_id == event_id))
    if existing:
        return existing
    touchpoint = db.get(Touchpoint, touchpoint_id)
    if not touchpoint or not touchpoint.active:
        raise HTTPException(status_code=422, detail="Điểm chạm không tồn tại hoặc đã ngừng hoạt động")
    observed_at = ensure_aware(observed_at)
    image_bytes = await read_image(image)
    try:
        result = await vision.analyze(image_bytes, image.filename or "image.jpg", image.content_type)
    except Exception as exc:
        observation = Observation(
            event_id=event_id,
            touchpoint_id=touchpoint.id,
            observed_at=observed_at,
            image_status="MODEL_ERROR",
            expression_status="NOT_RUN",
            identity_status="NOT_RUN",
            demo_data=demo_data,
        )
        db.add(observation)
        db.commit()
        raise HTTPException(status_code=502, detail="Dịch vụ xử lý ảnh không phản hồi") from exc

    customer = None
    distance = None
    identity_status = "NOT_RUN"
    visit = None
    if result.image_status == "VALID" and result.embedding:
        customer, distance, identity_status = match_customer(db, result.embedding)
        if customer:
            visit = get_or_create_visit(db, customer, observed_at, demo_data)
    observation = Observation(
        event_id=event_id,
        touchpoint_id=touchpoint.id,
        observed_at=observed_at,
        customer_id=customer.id if customer else None,
        visit_id=visit.id if visit else None,
        expression_label=result.expression_label,
        expression_confidence=result.expression_confidence,
        expression_scores=result.expression_scores,
        face_match_distance=distance,
        image_status=result.image_status,
        expression_status=result.expression_status,
        identity_status=identity_status,
        detector_version=result.models.get("detector"),
        emotion_model_version=result.models.get("emotion"),
        recognition_model_version=result.models.get("embedding"),
        demo_data=demo_data,
    )
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


@app.post("/api/v1/simulation/observations/batch", status_code=201)
def create_simulated_observations(
    payload: SimulatedObservationBatchInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.MANAGER, Role.ADMIN)),
):
    created = []
    skipped = 0
    for item in payload.observations:
        existing = db.scalar(select(Observation).where(Observation.event_id == item.event_id))
        if existing:
            skipped += 1
            created.append({"event_id": existing.event_id, "observation_id": existing.id, "visit_id": existing.visit_id})
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
        visit = get_or_create_visit(db, customer, observed_at, True) if customer else None
        observation = Observation(
            event_id=item.event_id,
            touchpoint_id=touchpoint.id,
            observed_at=observed_at,
            customer_id=customer.id if customer else None,
            visit_id=visit.id if visit else None,
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
    return {"visit": visit, "observations": observations}


@app.post("/api/v1/visits/{visit_id}/close")
def close_visit(visit_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    visit = db.get(Visit, visit_id)
    if not visit:
        raise HTTPException(status_code=404, detail="Không tìm thấy lượt ghé thăm")
    visit.status = VisitStatus.CLOSED
    visit.ended_at = visit.last_seen_at
    visit.close_reason = "MANUAL"
    db.commit()
    return visit


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
        .where(Observation.image_status == "VALID", Observation.expression_status == "VALID")
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
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    stmt = select(Observation.image_status, Observation.expression_status, Observation.identity_status, func.count(Observation.id))
    if from_time:
        stmt = stmt.where(Observation.observed_at >= ensure_aware(from_time))
    if to_time:
        stmt = stmt.where(Observation.observed_at <= ensure_aware(to_time))
    rows = db.execute(stmt.group_by(Observation.image_status, Observation.expression_status, Observation.identity_status)).all()
    return [
        {"image_status": image, "expression_status": expression, "identity_status": identity, "count": count}
        for image, expression, identity, count in rows
    ]


@app.get("/api/v1/reports/expression-changes")
def expression_changes(
    from_touchpoint_id: str | None = None,
    to_touchpoint_id: str | None = None,
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
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
    first_per_touchpoint: dict[tuple[str, str], Observation] = {}
    for row in rows:
        first_per_touchpoint.setdefault((row.visit_id, row.touchpoint_id), row)
    by_visit: dict[str, list[Observation]] = {}
    for row in first_per_touchpoint.values():
        by_visit.setdefault(row.visit_id, []).append(row)
    counts: dict[tuple[str, str, str, str], int] = {}
    for observations in by_visit.values():
        observations.sort(key=lambda item: (item.observed_at, item.id))
        for before, after in zip(observations, observations[1:]):
            if from_touchpoint_id and before.touchpoint_id != from_touchpoint_id:
                continue
            if to_touchpoint_id and after.touchpoint_id != to_touchpoint_id:
                continue
            key = (before.touchpoint_id, after.touchpoint_id, before.expression_label, after.expression_label)
            counts[key] = counts.get(key, 0) + 1
    return [
        {
            "from_touchpoint_id": key[0],
            "to_touchpoint_id": key[1],
            "from_label": key[2],
            "to_label": key[3],
            "count": count,
        }
        for key, count in sorted(counts.items())
    ]
