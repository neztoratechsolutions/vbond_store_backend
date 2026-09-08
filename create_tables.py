from app.database import Base, engine

# Import all models
from app.models.category import Category
from app.models.subcategory import Subcategory
from app.models.unit import Unit
from app.models.product import Product
from app.models.product_image import ProductImage

from app.models.stock import Stock
from app.models.stock_transaction import StockTransaction

from app.models.customer import Customer
from app.models.customer_address import CustomerAddress

from app.models.cart import Cart
from app.models.cart_item import CartItem

from app.models.offer import Offer


from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory


from app.models.delivery import Delivery
from app.models.user import User


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")


if __name__ == "__main__":
    create_tables()