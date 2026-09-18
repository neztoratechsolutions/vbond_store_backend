from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order
from app.models.order_item import OrderItem

from app.schemas.dashboard import (
    DashboardResponse,
    DashboardSummary,
    LatestOrder,
    TopProduct,
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


# ==========================================================
# DASHBOARD
# ==========================================================

@router.get(
    "",
    response_model=DashboardResponse
)
def get_dashboard(
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # CURRENT DATE / TIME
    # ------------------------------------------------------

    now = datetime.now(timezone.utc)

    today_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    tomorrow_start = today_start.replace(
        day=today_start.day
    )

    # Easier and safer calculation for tomorrow
    from datetime import timedelta

    tomorrow_start = today_start + timedelta(days=1)

    # First day of current month
    month_start = now.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )


    # ======================================================
    # REVENUE / ORDER FILTER
    # ======================================================

    # Cancelled orders should not be included in revenue.
    #
    # Change this list according to your business logic.

    valid_statuses = [
        "CONFIRMED",
        "PACKED",
        "OUT_FOR_DELIVERY",
        "DELIVERED"
    ]


    # ======================================================
    # TOTAL REVENUE
    # ======================================================

    total_revenue = (
        db.query(
            func.coalesce(
                func.sum(Order.total_amount),
                0
            )
        )
        .filter(
            Order.order_status.in_(valid_statuses)
        )
        .scalar()
    )

    total_revenue = Decimal(str(total_revenue or 0))


    # ======================================================
    # THIS MONTH REVENUE
    # ======================================================

    this_month_revenue = (
        db.query(
            func.coalesce(
                func.sum(Order.total_amount),
                0
            )
        )
        .filter(
            Order.order_status.in_(valid_statuses),
            Order.created_at >= month_start,
            Order.created_at < tomorrow_start
        )
        .scalar()
    )

    this_month_revenue = Decimal(
        str(this_month_revenue or 0)
    )


    # ======================================================
    # TOTAL ORDERS
    # ======================================================

    total_orders = (
        db.query(func.count(Order.id))
        .filter(
            Order.order_status.in_(valid_statuses)
        )
        .scalar()
    ) or 0


    # ======================================================
    # THIS MONTH ORDERS
    # ======================================================

    this_month_orders = (
        db.query(func.count(Order.id))
        .filter(
            Order.order_status.in_(valid_statuses),
            Order.created_at >= month_start,
            Order.created_at < tomorrow_start
        )
        .scalar()
    ) or 0


    # ======================================================
    # TODAY'S ORDERS
    # ======================================================

    today_orders = (
        db.query(func.count(Order.id))
        .filter(
            Order.order_status.in_(valid_statuses),
            Order.created_at >= today_start,
            Order.created_at < tomorrow_start
        )
        .scalar()
    ) or 0


    # ======================================================
    # TODAY'S REVENUE
    # ======================================================

    today_revenue = (
        db.query(
            func.coalesce(
                func.sum(Order.total_amount),
                0
            )
        )
        .filter(
            Order.order_status.in_(valid_statuses),
            Order.created_at >= today_start,
            Order.created_at < tomorrow_start
        )
        .scalar()
    )

    today_revenue = Decimal(
        str(today_revenue or 0)
    )


    # ======================================================
    # LATEST 5 ORDERS
    # ======================================================

    latest_orders_db = (
        db.query(Order)
        .order_by(
            desc(Order.created_at)
        )
        .limit(5)
        .all()
    )


    latest_orders = []

    for order in latest_orders_db:

        customer_name = ""

        if order.customer_details:
            customer_name = order.customer_details.get(
                "name",
                ""
            )

        latest_orders.append(
            LatestOrder(
                order_number=order.order_number,
                customer_name=customer_name,
                total_amount=Decimal(
                    str(order.total_amount or 0)
                ),
                payment_status=order.payment_status,
                order_status=order.order_status,
                created_at=order.created_at
            )
        )


    # ======================================================
    # TOP 5 PRODUCTS THIS MONTH
    # ======================================================

    top_products_db = (
        db.query(
            OrderItem.product_id,
            OrderItem.product_name,

            func.sum(
                OrderItem.quantity
            ).label(
                "quantity_sold"
            ),

            func.sum(
                OrderItem.total_price
            ).label(
                "revenue"
            )
        )
        .join(
            Order,
            Order.id == OrderItem.order_id
        )
        .filter(
            Order.order_status.in_(valid_statuses),
            Order.created_at >= month_start,
            Order.created_at < tomorrow_start
        )
        .group_by(
            OrderItem.product_id,
            OrderItem.product_name
        )
        .order_by(
            desc("quantity_sold")
        )
        .limit(5)
        .all()
    )


    top_products = []

    for product in top_products_db:

        top_products.append(
            TopProduct(
                product_id=product.product_id,
                product_name=product.product_name,
                quantity_sold=Decimal(
                    str(product.quantity_sold or 0)
                ),
                revenue=Decimal(
                    str(product.revenue or 0)
                )
            )
        )


    # ======================================================
    # FINAL RESPONSE
    # ======================================================

    return DashboardResponse(

        summary=DashboardSummary(
            total_revenue=total_revenue,
            this_month_revenue=this_month_revenue,
            total_orders=total_orders,
            this_month_orders=this_month_orders,
            today_orders=today_orders,
            today_revenue=today_revenue
        ),

        latest_orders=latest_orders,

        top_products_this_month=top_products
    )