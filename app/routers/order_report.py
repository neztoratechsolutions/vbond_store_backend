# =========================================================
# ORDER REPORT ROUTER
# =========================================================

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order
from app.models.order_item import OrderItem


router = APIRouter(
    prefix="/order-report",
    tags=["Order Report"]
)


# =========================================================
# GET ORDER REPORT
# GET /order-report
# =========================================================

@router.get("")
def get_order_report(
    from_date: Optional[date] = Query(
        default=None,
        description="Start date in YYYY-MM-DD format"
    ),
    to_date: Optional[date] = Query(
        default=None,
        description="End date in YYYY-MM-DD format"
    ),
    db: Session = Depends(get_db)
):

    # =====================================================
    # TIMEZONE
    # =====================================================

    india_timezone = ZoneInfo("Asia/Kolkata")
    utc_timezone = ZoneInfo("UTC")

    today = datetime.now(india_timezone).date()

    # =====================================================
    # DATE VALIDATION
    # =====================================================

    if from_date and to_date:

        if from_date > to_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="from_date cannot be greater than to_date"
            )

    # =====================================================
    # DETERMINE REPORT DATE RANGE
    #
    # No filter:
    #     Today
    #
    # from_date only:
    #     from_date -> Today
    #
    # to_date only:
    #     to_date only
    #
    # both:
    #     from_date -> to_date
    # =====================================================

    no_date_filter = (
        from_date is None
        and to_date is None
    )

    if no_date_filter:

        report_from_date = today
        report_to_date = today

    elif from_date is not None and to_date is None:

        report_from_date = from_date
        report_to_date = today

    elif from_date is None and to_date is not None:

        report_from_date = to_date
        report_to_date = to_date

    else:

        report_from_date = from_date
        report_to_date = to_date

    # =====================================================
    # INDIA DATE RANGE -> UTC
    # =====================================================

    start_india_datetime = datetime.combine(
        report_from_date,
        time.min
    ).replace(
        tzinfo=india_timezone
    )

    # End date inclusive
    # Use next day's midnight as upper limit
    end_india_datetime = datetime.combine(
        report_to_date + timedelta(days=1),
        time.min
    ).replace(
        tzinfo=india_timezone
    )

    start_utc_datetime = (
        start_india_datetime
        .astimezone(utc_timezone)
        .replace(tzinfo=None)
    )

    end_utc_datetime = (
        end_india_datetime
        .astimezone(utc_timezone)
        .replace(tzinfo=None)
    )

    # =====================================================
    # GET ORDERS
    # =====================================================

    orders = (
        db.query(Order)
        .filter(
            Order.is_active.is_(True),
            Order.created_at >= start_utc_datetime,
            Order.created_at < end_utc_datetime
        )
        .order_by(
            Order.created_at.desc()
        )
        .all()
    )

    # =====================================================
    # NO ORDERS FOUND
    # =====================================================

    if not orders:

        # -----------------------------------------------
        # NO FILTER = TODAY
        # -----------------------------------------------

        if no_date_filter:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No orders found for today "
                    f"({today.strftime('%Y-%m-%d')})"
                )
            )

        # -----------------------------------------------
        # FILTERED DATE RANGE
        # -----------------------------------------------

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No orders found for the selected date range"
        )

    # =====================================================
    # TOTAL ORDERS
    # =====================================================

    total_orders = len(orders)

    # =====================================================
    # TOTAL REVENUE
    # =====================================================

    total_revenue = sum(
        (
            order.total_amount or Decimal("0")
            for order in orders
        ),
        Decimal("0")
    )

    # =====================================================
    # PENDING ORDERS
    # =====================================================

    pending_orders = sum(
        1
        for order in orders
        if str(order.order_status).lower() == "pending"
    )

    # =====================================================
    # PAID ORDERS
    # =====================================================

    paid_orders = sum(
        1
        for order in orders
        if str(order.payment_status).lower() == "paid"
    )

    # =====================================================
    # GET ORDER ITEMS
    # =====================================================

    order_ids = [
        order.id
        for order in orders
    ]

    order_items = (
        db.query(OrderItem)
        .filter(
            OrderItem.order_id.in_(order_ids)
        )
        .all()
    )

    # =====================================================
    # PRODUCT-WISE SALES
    # =====================================================

    product_sales = {}

    for item in order_items:

        product_name = (
            item.product_name
            if item.product_name
            else "Unknown Product"
        )

        if product_name not in product_sales:

            product_sales[product_name] = {
                "product_name": product_name,
                "order_count": 0,
                "total_quantity": Decimal("0"),
                "revenue": Decimal("0")
            }

        product_sales[product_name]["order_count"] += 1

        product_sales[product_name]["total_quantity"] += (
            item.quantity or Decimal("0")
        )

        product_sales[product_name]["revenue"] += (
            item.total_price or Decimal("0")
        )

    product_wise_sales = list(
        product_sales.values()
    )

    # Highest revenue first
    product_wise_sales.sort(
        key=lambda item: item["revenue"],
        reverse=True
    )

    # =====================================================
    # CURRENT MONTH REPORT
    #
    # Current month is always calculated separately.
    #
    # Example:
    # Today = 17-09-2026
    #
    # Month:
    # 01-09-2026 -> 17-09-2026
    # =====================================================

    month_start_date = today.replace(day=1)

    month_start_india_datetime = datetime.combine(
        month_start_date,
        time.min
    ).replace(
        tzinfo=india_timezone
    )

    month_end_india_datetime = datetime.combine(
        today + timedelta(days=1),
        time.min
    ).replace(
        tzinfo=india_timezone
    )

    month_start_utc_datetime = (
        month_start_india_datetime
        .astimezone(utc_timezone)
        .replace(tzinfo=None)
    )

    month_end_utc_datetime = (
        month_end_india_datetime
        .astimezone(utc_timezone)
        .replace(tzinfo=None)
    )

    month_orders = (
        db.query(Order)
        .filter(
            Order.is_active.is_(True),
            Order.created_at >= month_start_utc_datetime,
            Order.created_at < month_end_utc_datetime
        )
        .all()
    )

    month_total_orders = len(month_orders)

    month_revenue = sum(
        (
            order.total_amount or Decimal("0")
            for order in month_orders
        ),
        Decimal("0")
    )

    # =====================================================
    # ORDER LIST
    # =====================================================

    order_list = []

    for order in orders:

        order_list.append({
            "id": order.id,
            "order_number": order.order_number,
            "customer_details": order.customer_details,
            "subtotal": order.subtotal,
            "discount_amount": order.discount_amount,
            "tax_amount": order.tax_amount,
            "delivery_charge": order.delivery_charge,
            "total_amount": order.total_amount,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "order_status": order.order_status,
            "customer_note": order.customer_note,
            "created_at": order.created_at,
            "updated_at": order.updated_at
        })

    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {
        "status_code": 200,
        "message": "Order report retrieved successfully",

        # -------------------------------------------------
        # FILTER
        # -------------------------------------------------

        "filters": {
            "from_date": report_from_date,
            "to_date": report_to_date
        },

        # -------------------------------------------------
        # SELECTED DATE RANGE SUMMARY
        # -------------------------------------------------

        "summary": {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "pending_orders": pending_orders,
            "paid_orders": paid_orders
        },

        # -------------------------------------------------
        # CURRENT MONTH SUMMARY
        # -------------------------------------------------

        "current_month": {
            "month": today.strftime("%B %Y"),
            "from_date": month_start_date,
            "to_date": today,
            "total_orders": month_total_orders,
            "revenue": month_revenue
        },

        # -------------------------------------------------
        # PRODUCT-WISE SALES
        # -------------------------------------------------

        "product_wise_sales": product_wise_sales,

        # -------------------------------------------------
        # ORDERS
        # -------------------------------------------------

        "count": total_orders,

        "orders": order_list
    }



# ==========================================================
# GET ITEM WISE REPORT
# GET /order-report/item-wise
# ==========================================================

@router.get("/item-wise")
def get_item_wise_report(
    from_date: Optional[date] = Query(
        default=None,
        description="Start date in YYYY-MM-DD format"
    ),
    to_date: Optional[date] = Query(
        default=None,
        description="End date in YYYY-MM-DD format"
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number"
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of items per page"
    ),
    db: Session = Depends(get_db)
):

    # ======================================================
    # TIMEZONE
    # ======================================================

    india_timezone = ZoneInfo("Asia/Kolkata")
    utc_timezone = ZoneInfo("UTC")

    today = datetime.now(
        india_timezone
    ).date()

    # ======================================================
    # DATE VALIDATION
    # ======================================================

    if from_date and to_date:

        if from_date > to_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="from_date cannot be greater than to_date"
            )

    # ======================================================
    # DETERMINE DATE RANGE
    #
    # No filter:
    #     Today
    #
    # from_date only:
    #     from_date -> Today
    #
    # to_date only:
    #     to_date only
    #
    # both:
    #     from_date -> to_date
    # ======================================================

    no_date_filter = (
        from_date is None
        and to_date is None
    )

    if no_date_filter:

        report_from_date = today
        report_to_date = today

    elif from_date is not None and to_date is None:

        report_from_date = from_date
        report_to_date = today

    elif from_date is None and to_date is not None:

        report_from_date = to_date
        report_to_date = to_date

    else:

        report_from_date = from_date
        report_to_date = to_date

    # ======================================================
    # INDIA DATE RANGE -> UTC
    # ======================================================

    start_india_datetime = datetime.combine(
        report_from_date,
        time.min
    ).replace(
        tzinfo=india_timezone
    )

    # End date inclusive
    end_india_datetime = datetime.combine(
        report_to_date + timedelta(days=1),
        time.min
    ).replace(
        tzinfo=india_timezone
    )

    start_utc_datetime = (
        start_india_datetime
        .astimezone(utc_timezone)
        .replace(tzinfo=None)
    )

    end_utc_datetime = (
        end_india_datetime
        .astimezone(utc_timezone)
        .replace(tzinfo=None)
    )

    # ======================================================
    # GET ACTIVE ORDERS
    # ======================================================

    orders = (
        db.query(Order.id)
        .filter(
            Order.is_active.is_(True),
            Order.created_at >= start_utc_datetime,
            Order.created_at < end_utc_datetime
        )
        .all()
    )

    # ======================================================
    # NO ORDERS
    # ======================================================

    if not orders:

        if no_date_filter:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"No orders found for today "
                    f"({today.strftime('%Y-%m-%d')})"
                )
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No orders found for the selected date range"
        )

    order_ids = [
        order.id
        for order in orders
    ]

    # ======================================================
    # GET ORDER ITEMS
    # ======================================================

    order_items = (
        db.query(OrderItem)
        .filter(
            OrderItem.order_id.in_(order_ids)
        )
        .all()
    )

    if not order_items:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No item sales found for the selected date range"
        )

    # ======================================================
    # ITEM WISE SALES
    # ======================================================

    item_sales = {}

    for item in order_items:

        product_name = (
            item.product_name
            if item.product_name
            else "Unknown Product"
        )

        if product_name not in item_sales:

            item_sales[product_name] = {
                "product_name": product_name,
                "order_count": 0,
                "total_quantity": Decimal("0"),
                "revenue": Decimal("0")
            }

        item_sales[product_name]["order_count"] += 1

        item_sales[product_name]["total_quantity"] += (
            item.quantity
            if item.quantity is not None
            else Decimal("0")
        )

        item_sales[product_name]["revenue"] += (
            item.total_price
            if item.total_price is not None
            else Decimal("0")
        )

    # ======================================================
    # CONVERT TO LIST
    # ======================================================

    items = list(
        item_sales.values()
    )

    # Highest revenue first
    items.sort(
        key=lambda item: item["revenue"],
        reverse=True
    )

    # ======================================================
    # TOTALS
    # ======================================================

    total_items = len(items)

    total_quantity = sum(
        (
            item["total_quantity"]
            for item in items
        ),
        Decimal("0")
    )

    total_revenue = sum(
        (
            item["revenue"]
            for item in items
        ),
        Decimal("0")
    )

    # ======================================================
    # PAGINATION
    # ======================================================

    offset = (page - 1) * limit

    paginated_items = items[
        offset:offset + limit
    ]

    if not paginated_items:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No items found for this page"
        )

    total_pages = (
        total_items + limit - 1
    ) // limit

    # ======================================================
    # RESPONSE
    # ======================================================

    return {
        "status_code": 200,
        "message": "Item wise report retrieved successfully",

        "filters": {
            "from_date": report_from_date,
            "to_date": report_to_date
        },

        "summary": {
            "total_items": total_items,
            "total_quantity": total_quantity,
            "total_revenue": total_revenue
        },

        "pagination": {
            "current_page": page,
            "per_page": limit,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next_page": page < total_pages,
            "has_previous_page": page > 1
        },

        "count": len(paginated_items),

        "items": paginated_items
    }