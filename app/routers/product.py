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


@router.get(
    "",
    response_model=list[ProductResponse]
)
def get_products(
    db: Session = Depends(get_db)
):
    results = (
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
        .order_by(
            Product.display_order.asc(),
            Product.id.desc()
        )
        .all()
    )

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

    return response

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