from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_revenue: Decimal
    this_month_revenue: Decimal
    total_orders: int
    this_month_orders: int
    today_orders: int
    today_revenue: Decimal


class LatestOrder(BaseModel):
    order_number: str
    customer_name: str
    total_amount: Decimal
    payment_status: str
    order_status: str
    created_at: datetime


class TopProduct(BaseModel):
    product_id: int
    product_name: str
    quantity_sold: Decimal
    revenue: Decimal


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    latest_orders: list[LatestOrder]
    top_products_this_month: list[TopProduct]