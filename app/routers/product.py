import re
from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.models.unit import Unit
from app.models.subcategory import Subcategory
from app.schemas.product import ProductCreate,ProductResponse

router = APIRouter(
    prefix = "/products",
    tags = ["Products"]
)

def generate_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)

    return slug

@router.post(
    "",
    response_model = ProductResponse,
    status_code = status.HTTP_201_CREATED
)
def create_product(
    data : ProductCreate,
    db : Session = Depends(get_db)
):
    #check subcategory
    subcategory = db.query(Subcategory).filter(
        Subcategory.id == data.subcategory_id
    ).first()

    if not subcategory:
        raise HTTPException(
            status_code = 404,
            detail = "Subcategory not found"
        )

    #check Unit
    unit = db.query(Unit).filter(
        Unit.id == data.unit_id
    ).first()

    if not unit:
            raise HTTPException(
                status_code = 404,
                detail = "unit not found"
            )

    #check sku
    existing_sku = db.query(Product).filter(
         Product.sku == data . sku
    ).first()

    if existing_sku:
        raise HTTPException(
            status_code=400,
            detail="SKU already exists"
        )

    # Generate slug automatically
    slug = generate_slug(data.name)

    # Check duplicate slug
    existing_slug = (
        db.query(Product)
        .filter(Product.slug == slug)
        .first()
    )

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