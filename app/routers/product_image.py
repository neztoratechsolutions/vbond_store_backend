# 
import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session
from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import Query

from app.database import get_db
from app.models.product import Product
from app.models.product_image import ProductImage
from app.schemas.product_image import ProductImageUpdate


router = APIRouter(
    prefix="/product-images",
    tags=["Product Images"]
)


# ==========================================================
# UPLOAD DIRECTORY
# ==========================================================

UPLOAD_DIR = "uploads/product_images"

os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==========================================================
# POST - BULK UPLOAD PRODUCT IMAGES
# ==========================================================

@router.post("/bulk", status_code=201)
async def create_product_images(
    product_id: int = Form(...),
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # CHECK PRODUCT
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # CHECK IMAGES
    # ------------------------------------------------------

    if not images:
        raise HTTPException(
            status_code=400,
            detail="At least one image is required"
        )

    # ------------------------------------------------------
    # GET CURRENT MAX DISPLAY ORDER
    # ------------------------------------------------------

    last_image = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id)
        .order_by(ProductImage.display_order.desc())
        .first()
    )

    if last_image:
        display_order = last_image.display_order + 1
    else:
        display_order = 1

    created_images = []

    # ------------------------------------------------------
    # SAVE MULTIPLE IMAGES
    # ------------------------------------------------------

    for image_file in images:

        if not image_file.filename:
            continue

        # Get extension
        extension = os.path.splitext(
            image_file.filename
        )[1].lower()

        # Allow only image files
        allowed_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp"
        ]

        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid image format: "
                    f"{image_file.filename}"
                )
            )

        # Generate unique filename
        filename = (
            f"{uuid.uuid4().hex}"
            f"{extension}"
        )

        file_path = os.path.join(
            UPLOAD_DIR,
            filename
        )

        # Save file
        with open(file_path, "wb") as buffer:
            content = await image_file.read()
            buffer.write(content)

        # --------------------------------------------------
        # SAVE IMAGE PATH IN DATABASE
        # --------------------------------------------------

        product_image = ProductImage(
            product_id=product_id,
            image=file_path.replace("\\", "/"),
            display_order=display_order
        )

        db.add(product_image)

        created_images.append(product_image)

        display_order += 1

    if not created_images:
        raise HTTPException(
            status_code=400,
            detail="No valid images uploaded"
        )

    db.commit()

    for product_image in created_images:
        db.refresh(product_image)

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return {
        "message": "Product images uploaded successfully",
        "product_id": product_id,
        "images": [
            {
                "id": image.id,
                "product_id": image.product_id,
                "image": image.image,
                "display_order": image.display_order
            }
            for image in created_images
        ]
    }

# ==========================================================
# GET - ALL PRODUCT IMAGES
# Pagination + Date Filter
# ==========================================================

@router.get("/")
def get_all_product_images(
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
        description="Number of product images per page"
    ),
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # VALIDATE DATE RANGE
    # ------------------------------------------------------

    if start_date and end_date:
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date cannot be greater than end_date"
            )

    # ------------------------------------------------------
    # BASE QUERY
    # ------------------------------------------------------

    images_query = db.query(ProductImage)

    # ------------------------------------------------------
    # DATE FILTER
    # ------------------------------------------------------

    if start_date or end_date:

        india_timezone = ZoneInfo("Asia/Kolkata")

        if start_date is None:
            start_date = end_date

        if end_date is None:
            end_date = start_date

        start_india_datetime = datetime.combine(
            start_date,
            time.min
        ).replace(
            tzinfo=india_timezone
        )

        # end_date is inclusive
        end_india_datetime = datetime.combine(
            end_date + timedelta(days=1),
            time.min
        ).replace(
            tzinfo=india_timezone
        )

        start_utc_datetime = start_india_datetime.astimezone(
            ZoneInfo("UTC")
        ).replace(
            tzinfo=None
        )

        end_utc_datetime = end_india_datetime.astimezone(
            ZoneInfo("UTC")
        ).replace(
            tzinfo=None
        )

        images_query = images_query.filter(
            ProductImage.created_at >= start_utc_datetime,
            ProductImage.created_at < end_utc_datetime
        )

    # ------------------------------------------------------
    # ORDER BY
    # ------------------------------------------------------

    images_query = images_query.order_by(
        ProductImage.product_id.asc(),
        ProductImage.display_order.asc(),
        ProductImage.id.asc()
    )

    # ------------------------------------------------------
    # TOTAL COUNT
    # ------------------------------------------------------

    total_images = images_query.count()

    if total_images == 0:
        raise HTTPException(
            status_code=404,
            detail="No product images found for the selected date range"
        )

    # ------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------

    offset = (page - 1) * limit

    images = (
        images_query
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not images:
        raise HTTPException(
            status_code=404,
            detail="No product images found for this page"
        )

    total_pages = (
        total_images + limit - 1
    ) // limit

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "Product images retrieved successfully",

        "filters": {
            "start_date": start_date,
            "end_date": end_date
        },

        "pagination": {
            "current_page": page,
            "per_page": limit,
            "total_images": total_images,
            "total_pages": total_pages,
            "has_next_page": page < total_pages,
            "has_previous_page": page > 1
        },

        "count": len(images),
        "data": images
    }


# ==========================================================
# GET - IMAGES BY PRODUCT ID
# ==========================================================

@router.get("/product/{product_id}")
def get_product_images(
    product_id: int,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # CHECK PRODUCT
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # GET IMAGES
    # ------------------------------------------------------

    images = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id)
        .order_by(ProductImage.display_order)
        .all()
    )

    if not images:
        raise HTTPException(
            status_code=404,
            detail="No images found for this product"
        )

    return {
        "message": "Product images retrieved successfully",
        "product_id": product_id,
        "data": images
    }


# ==========================================================
# GET - SINGLE PRODUCT IMAGE
# ==========================================================

@router.get("/{image_id}")
def get_product_image(
    image_id: int,
    db: Session = Depends(get_db)
):

    image = (
        db.query(ProductImage)
        .filter(ProductImage.id == image_id)
        .first()
    )

    if not image:
        raise HTTPException(
            status_code=404,
            detail="Product image not found"
        )

    return {
        "message": "Product image retrieved successfully",
        "data": image
    }


# ==========================================================
# PUT - UPDATE PRODUCT IMAGE
# ==========================================================

@router.put("/{image_id}")
def update_product_image(
    image_id: int,
    data: ProductImageUpdate,
    db: Session = Depends(get_db)
):

    image = (
        db.query(ProductImage)
        .filter(ProductImage.id == image_id)
        .first()
    )

    if not image:
        raise HTTPException(
            status_code=404,
            detail="Product image not found"
        )

    # ------------------------------------------------------
    # UPDATE DISPLAY ORDER
    # ------------------------------------------------------

    if data.display_order is not None:

        if data.display_order < 0:
            raise HTTPException(
                status_code=400,
                detail="Display order cannot be negative"
            )

        image.display_order = data.display_order

    db.commit()
    db.refresh(image)

    return {
        "message": "Product image updated successfully",
        "data": image
    }


# ==========================================================
# DELETE - PRODUCT IMAGE
# ==========================================================

@router.delete("/{image_id}")
def delete_product_image(
    image_id: int,
    db: Session = Depends(get_db)
):

    image = (
        db.query(ProductImage)
        .filter(ProductImage.id == image_id)
        .first()
    )

    if not image:
        raise HTTPException(
            status_code=404,
            detail="Product image not found"
        )

    # ------------------------------------------------------
    # DELETE PHYSICAL FILE
    # ------------------------------------------------------

    if image.image and os.path.exists(image.image):
        os.remove(image.image)

    # ------------------------------------------------------
    # DELETE DATABASE RECORD
    # ------------------------------------------------------

    db.delete(image)
    db.commit()

    return {
        "message": "Product image deleted successfully"
    }