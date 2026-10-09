from __future__ import annotations

import argparse

from sqlalchemy import delete, select

from app.database import SessionLocal
from app.models import (
    CaptureEvent,
    Customer,
    FaceTemplate,
    Observation,
    Order,
    OrderItem,
    Product,
    ProductCategory,
    SequenceAnalysisRun,
    SequenceClusterAssignment,
    SequenceClusterSummary,
    Touchpoint,
    Visit,
)


def main(confirm: str) -> None:
    if confirm != "RESET-DEMO":
        raise SystemExit("Lệnh chỉ chạy khi truyền --confirm RESET-DEMO")
    with SessionLocal() as db:
        demo_customer_ids = list(db.scalars(select(Customer.id).where(Customer.demo_data.is_(True))))
        demo_order_ids = list(db.scalars(select(Order.id).where(Order.demo_data.is_(True))))
        demo_visit_ids = list(db.scalars(select(Visit.id).where(Visit.demo_data.is_(True))))
        demo_analysis_ids = (
            list(
                db.scalars(
                    select(SequenceClusterAssignment.run_id)
                    .where(SequenceClusterAssignment.visit_id.in_(demo_visit_ids))
                    .distinct()
                )
            )
            if demo_visit_ids
            else []
        )
        if demo_analysis_ids:
            db.execute(delete(SequenceClusterAssignment).where(SequenceClusterAssignment.run_id.in_(demo_analysis_ids)))
            db.execute(delete(SequenceClusterSummary).where(SequenceClusterSummary.run_id.in_(demo_analysis_ids)))
            db.execute(delete(SequenceAnalysisRun).where(SequenceAnalysisRun.id.in_(demo_analysis_ids)))
        elif demo_visit_ids:
            db.execute(delete(SequenceClusterAssignment).where(SequenceClusterAssignment.visit_id.in_(demo_visit_ids)))
            db.execute(delete(SequenceClusterSummary).where(SequenceClusterSummary.medoid_visit_id.in_(demo_visit_ids)))
        if demo_order_ids:
            db.execute(delete(OrderItem).where(OrderItem.order_id.in_(demo_order_ids)))
        db.execute(delete(Order).where(Order.demo_data.is_(True)))
        db.execute(delete(Observation).where(Observation.demo_data.is_(True)))
        db.execute(delete(CaptureEvent).where(CaptureEvent.demo_data.is_(True)))
        db.execute(delete(Visit).where(Visit.demo_data.is_(True)))
        if demo_customer_ids:
            db.execute(delete(FaceTemplate).where(FaceTemplate.customer_id.in_(demo_customer_ids)))
        db.execute(delete(Product).where(Product.demo_data.is_(True)))
        db.execute(delete(ProductCategory).where(ProductCategory.demo_data.is_(True)))
        db.execute(delete(Touchpoint).where(Touchpoint.demo_data.is_(True)))
        db.execute(delete(Customer).where(Customer.demo_data.is_(True)))
        db.commit()
    print("Đã xóa dữ liệu có cờ demo_data=true")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    args = parser.parse_args()
    main(args.confirm)
