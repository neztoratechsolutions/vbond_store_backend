# import re
# from fastapi import APIRouter,Depends,HTTPException,status
# from sqlalchemy.orm import Session

# from app.database import get_db
# from app.models.product import Product
# from app.models.unit import Unit
# from app.models.subcategory import Subcategory
# from app.schemas.product import ProductCreate,ProductResponse

# router = APIRouter(
#     prefix = "/products",
#     tags = ["Products"]
# )

# def generate_slug(name: str) -> str:
#     slug = name.lower().strip()
#     slug = re.sub(r"[^a-z0-9\s-]", "", slug)
#     slug = re.sub(r"\s+", "-", slug)
#     slug = re.sub(r"-+", "-", slug)

#     return slug

# @router.post(
#     "",
#     response_model = ProductResponse,
#     status_code = status.HTTP_201_CREATED
# )
# def create_product(
#     data : ProductCreate,
#     db : Session = Depends(get_db)
# ):
#     #check subcategory
#     subcategory = db.query(Subcategory).filter(
#         Subcategory.id == data.subcategory_id
#     ).first()

#     if not subcategory:
#         raise HTTPException(
#             status_code = 404,
#             detail = "Subcategory not found"
#         )

#     #check Unit
#     unit = db.query(Unit).filter(
#         Unit.id == data.unit_id
#     ).first()

#     if not unit:
#             raise HTTPException(
#                 status_code = 404,
#                 detail = "unit not found"
#             )

#     #check sku
#     existing_sku = db.query(Product).filter(
#          Product.sku == data . sku
#     ).first()

#     if existing_sku:
#         raise HTTPException(
#             status_code=400,
#             detail="SKU already exists"
#         )

#     # Generate slug automatically
#     slug = generate_slug(data.name)

#     # Check duplicate slug
#     existing_slug = (
#         db.query(Product)
#         .filter(Product.slug == slug)
#         .first()
#     )

#     if existing_slug:
#         slug = f"{slug}-{data.sku.lower()}"

#     # Create Product
#     product = Product(
#         subcategory_id=data.subcategory_id,
#         unit_id=data.unit_id,
#         name=data.name,
#         slug=slug,
#         description=data.description,
#         sku=data.sku,
#         price=data.price,
#         mrp=data.mrp,
#         discount_price=data.discount_price,
#         tax_percentage=data.tax_percentage,
#         is_available=data.is_available,
#         is_active=data.is_active,
#         display_order=data.display_order
#     )

#     db.add(product)
#     db.commit()
#     db.refresh(product)

#     return product
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session,joinedload

from app.database import get_db
from app.models.product import Product
from app.models.unit import Unit
from app.models.subcategory import Subcategory
from app.schemas.product import ProductCreate, ProductResponse
from app.models.category import Category
from app.models.product_image import ProductImage
router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


def generate_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)

    return slug


# =========================================================
# CREATE PRODUCT
# POST /products
# =========================================================

@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db)
):
    # Check Subcategory
    subcategory = db.query(Subcategory).filter(
        Subcategory.id == data.subcategory_id
    ).first()

    if not subcategory:
        raise HTTPException(
            status_code=404,
            detail="Subcategory not found"
        )

    # Check Unit
    unit = db.query(Unit).filter(
        Unit.id == data.unit_id
    ).first()

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found"
        )

    # Check SKU
    existing_sku = db.query(Product).filter(
        Product.sku == data.sku
    ).first()

    if existing_sku:
        raise HTTPException(
            status_code=400,
            detail="SKU already exists"
        )

    # Generate slug
    slug = generate_slug(data.name)

    # Check duplicate slug
    existing_slug = db.query(Product).filter(
        Product.slug == slug
    ).first()

    if existing_slug:
        slug = f"{slug}-{data.sku.lower()}"

    # Create Product
    product = Product(
        subcategory_id=data.subcategory_id,
        unit_id=data.unit_id,
        name=data.name,
        slug=slug,
        description=data.description,
        sku=data.sku,
        price=data.price,
        mrp=data.mrp,
        discount_price=data.discount_price,
        tax_percentage=data.tax_percentage,
        is_available=data.is_available,
        is_active=data.is_active,
        display_order=data.display_order
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


# =========================================================
# GET ALL PRODUCTS
# GET /products
# =========================================================

from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import Query


@router.get("")
def get_products(
    start_date: Optional[date] = Query(
        default=None,
        description="Start date in YYYY-MM-DD format"
    ),
    end_date: Optional[date] = Query(
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
        description="Number of products per page"
    ),
    db: Session = Depends(get_db)
):

    # =====================================================
    # DATE VALIDATION
    # =====================================================

    if start_date and end_date:
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date cannot be greater than end_date"
            )

    # =====================================================
    # BASE QUERY
    # =====================================================

    products_query = (
        db.query(
            Product,
            Subcategory,
            Category
        )
        .join(
            Subcategory,
            Product.subcategory_id == Subcategory.id
        )
        .join(
            Category,
            Subcategory.category_id == Category.id
        )
    )

    # =====================================================
    # DATE FILTER
    # INDIA DATE -> UTC
    # =====================================================

    if start_date or end_date:

        india_timezone = ZoneInfo("Asia/Kolkata")

        # If only one date is provided,
        # use the same date for both
        if start_date is None:
            start_date = end_date

        if end_date is None:
            end_date = start_date

        # Start of start_date in India
        start_india_datetime = datetime.combine(
            start_date,
            time.min
        ).replace(
            tzinfo=india_timezone
        )

        # Start of the day AFTER end_date
        # This makes end_date inclusive
        end_india_datetime = datetime.combine(
            end_date + timedelta(days=1),
            time.min
        ).replace(
            tzinfo=india_timezone
        )

        # Convert India time to UTC
        start_utc_datetime = (
            start_india_datetime
            .astimezone(ZoneInfo("UTC"))
            .replace(tzinfo=None)
        )

        end_utc_datetime = (
            end_india_datetime
            .astimezone(ZoneInfo("UTC"))
            .replace(tzinfo=None)
        )

        products_query = products_query.filter(
            Product.created_at >= start_utc_datetime,
            Product.created_at < end_utc_datetime
        )

    # =====================================================
    # ORDER BY
    # =====================================================

    products_query = products_query.order_by(
        Product.display_order.asc(),
        Product.id.desc()
    )

    # =====================================================
    # TOTAL COUNT
    # =====================================================

    total_products = products_query.count()

    if total_products == 0:

        if start_date or end_date:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No products found for the selected date range"
            )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No products found"
        )

    # =====================================================
    # PAGINATION
    # =====================================================

    offset = (page - 1) * limit

    results = (
        products_query
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Page doesn't contain data
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No products found for this page"
        )

    # =====================================================
    # TOTAL PAGES
    # =====================================================

    total_pages = (
        total_products + limit - 1
    ) // limit

    # =====================================================
    # RESPONSE
    # =====================================================

    response = []

    for product, subcategory, category in results:

        product_data = {
            "id": product.id,
            "subcategory_id": product.subcategory_id,
            "unit_id": product.unit_id,
            "name": product.name,
            "slug": product.slug,
            "description": product.description,
            "sku": product.sku,
            "price": product.price,
            "mrp": product.mrp,
            "discount_price": product.discount_price,
            "tax_percentage": product.tax_percentage,
            "is_available": product.is_available,
            "is_active": product.is_active,
            "display_order": product.display_order,

            "created_at": product.created_at,
            "updated_at": product.updated_at,

            "subcategory": {
                "id": subcategory.id,
                "name": subcategory.name,

                "category": {
                    "id": category.id,
                    "name": category.name
                }
            }
        }

        response.append(product_data)

    return {
        "status_code": 200,
        "message": "Products retrieved successfully",

        "filters": {
            "start_date": start_date,
            "end_date": end_date
        },

        "pagination": {
            "current_page": page,
            "per_page": limit,
            "total_products": total_products,
            "total_pages": total_pages,
            "has_next_page": page < total_pages,
            "has_previous_page": page > 1
        },

        "count": len(response),

        "data": response
    }

# =========================================================
# GET SINGLE PRODUCT
# GET /products/{product_id}
# =========================================================

@router.get(
    "/{product_id}",
    response_model=ProductResponse
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# =========================================================
# UPDATE PRODUCT
# PUT /products/{product_id}
# =========================================================

@router.put(
    "/{product_id}",
    response_model=ProductResponse
)
def update_product(
    product_id: int,
    data: ProductCreate,
    db: Session = Depends(get_db)
):
    # Find Product
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Check Subcategory
    subcategory = (
        db.query(Subcategory)
        .filter(Subcategory.id == data.subcategory_id)
        .first()
    )

    if not subcategory:
        raise HTTPException(
            status_code=404,
            detail="Subcategory not found"
        )

    # Check Unit
    unit = (
        db.query(Unit)
        .filter(Unit.id == data.unit_id)
        .first()
    )

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found"
        )

    # Check SKU
    existing_sku = (
        db.query(Product)
        .filter(
            Product.sku == data.sku,
            Product.id != product_id
        )
        .first()
    )

    if existing_sku:
        raise HTTPException(
            status_code=400,
            detail="SKU already exists"
        )

    # Generate slug
    slug = generate_slug(data.name)

    # Check duplicate slug
    existing_slug = (
        db.query(Product)
        .filter(
            Product.slug == slug,
            Product.id != product_id
        )
        .first()
    )

    if existing_slug:
        slug = f"{slug}-{data.sku.lower()}"

    # Update Product
    product.subcategory_id = data.subcategory_id
    product.unit_id = data.unit_id
    product.name = data.name
    product.slug = slug
    product.description = data.description
    product.sku = data.sku
    product.price = data.price
    product.mrp = data.mrp
    product.discount_price = data.discount_price
    product.tax_percentage = data.tax_percentage
    product.is_available = data.is_available
    product.is_active = data.is_active
    product.display_order = data.display_order

    db.commit()
    db.refresh(product)

    # Get updated subcategory
    subcategory = (
        db.query(Subcategory)
        .filter(Subcategory.id == product.subcategory_id)
        .first()
    )

    # Get category through subcategory
    category = (
        db.query(Category)
        .filter(Category.id == subcategory.category_id)
        .first()
    )

    # Build response manually
    return {
        "id": product.id,
        "subcategory_id": product.subcategory_id,
        "unit_id": product.unit_id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "sku": product.sku,
        "price": product.price,
        "mrp": product.mrp,
        "discount_price": product.discount_price,
        "tax_percentage": product.tax_percentage,
        "is_available": product.is_available,
        "is_active": product.is_active,
        "display_order": product.display_order,
        "created_at": product.created_at,
        "updated_at": product.updated_at,

        "subcategory": {
            "id": subcategory.id,
            "name": subcategory.name,

            "category": {
                "id": category.id,
                "name": category.name
            }
        }
    }

# =========================================================
# DELETE PRODUCT
# DELETE /products/{product_id}
# =========================================================

@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    # Find Product
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Delete Product
    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully",
        "product_id": product_id
    }

#------------Product with their images-------------#
@router.get("/products/images")
def get_products_with_images(
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # GET ONLY ACTIVE PRODUCTS
    # ------------------------------------------------------

    products = (
        db.query(Product)
        .filter(Product.is_active.is_(True))
        .order_by(Product.id.desc())
        .all()
    )

    # ------------------------------------------------------
    # CHECK PRODUCTS
    # ------------------------------------------------------

    if not products:
        raise HTTPException(
            status_code=404,
            detail="No active products found"
        )

    result = []

    # ------------------------------------------------------
    # GET EACH PRODUCT WITH ITS IMAGES
    # ------------------------------------------------------

    for product in products:

        images = (
            db.query(ProductImage)
            .filter(
                ProductImage.product_id == product.id
            )
            .order_by(
                ProductImage.display_order.asc()
            )
            .all()
        )

        result.append({
            "id": product.id,
            "subcategory_id": product.subcategory_id,
            "unit_id": product.unit_id,

            "name": product.name,
            "slug": product.slug,
            "description": product.description,
            "sku": product.sku,

            "price": product.price,
            "mrp": product.mrp,
            "discount_price": product.discount_price,
            "tax_percentage": product.tax_percentage,

            "is_available": product.is_available,
            "is_active": product.is_active,
            "display_order": product.display_order,

            "created_at": product.created_at,
            "updated_at": product.updated_at,

            # --------------------------------------------------
            # ONLY THIS PRODUCT'S IMAGES
            # --------------------------------------------------

            "images": [
                {
                    "id": image.id,
                    "image": image.image,
                    "display_order": image.display_order
                }
                for image in images
            ]
        })

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return {
        "message": "Active products retrieved successfully",
        "data": result
    }