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
# ==========================================================

@router.get("/")
def get_all_product_images(
    db: Session = Depends(get_db)
):

    images = (
        db.query(ProductImage)
        .order_by(
            ProductImage.product_id,
            ProductImage.display_order
        )
        .all()
    )

    if not images:
        raise HTTPException(
            status_code=404,
            detail="No product images found"
        )

    return {
        "message": "Product images retrieved successfully",
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