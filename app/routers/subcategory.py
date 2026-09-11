# ==========================================================
# SUBCATEGORY ROUTER
# ==========================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

import re

from app.database import get_db

from app.models.subcategory import Subcategory
from app.models.category import Category

from app.schemas.subcategory import (
    SubcategoryBulkCreate,
    SubcategoryUpdate
)


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/subcategories",
    tags=["Subcategories"]
)


# ==========================================================
# POST - BULK CREATE SUBCATEGORIES
# ==========================================================

@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED
)
def create_subcategories(
    data: SubcategoryBulkCreate,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # Check subcategory list
    # ------------------------------------------------------

    if not data.subcategories:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one subcategory is required"
        )

    created_subcategories = []

    # ------------------------------------------------------
    # Loop through subcategories
    # ------------------------------------------------------

    for index, subcategory_data in enumerate(
        data.subcategories,
        start=1
    ):

        category_id = subcategory_data.category_id
        name = subcategory_data.name.strip()

        # --------------------------------------------------
        # Validate name
        # --------------------------------------------------

        if not name:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subcategory {index} name cannot be empty"
            )

        # --------------------------------------------------
        # Check parent category
        # --------------------------------------------------

        parent_category = (
            db.query(Category)
            .filter(
                Category.id == category_id
            )
            .first()
        )

        if not parent_category:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with ID {category_id} not found"
            )

        # --------------------------------------------------
        # Check duplicate subcategory name
        # Same name can exist under different categories
        # --------------------------------------------------

        existing_subcategory = (
            db.query(Subcategory)
            .filter(
                Subcategory.category_id == category_id,
                Subcategory.name.ilike(name)
            )
            .first()
        )

        if existing_subcategory:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Subcategory '{name}' already exists "
                    f"under category '{parent_category.name}'"
                )
            )

        # --------------------------------------------------
        # Generate slug
        # --------------------------------------------------

        slug = re.sub(
            r"[^a-z0-9]+",
            "-",
            name.lower()
        ).strip("-")

        if not slug:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subcategory name '{name}'"
            )

        # --------------------------------------------------
        # Check duplicate slug
        # --------------------------------------------------

        existing_slug = (
            db.query(Subcategory)
            .filter(
                Subcategory.slug == slug
            )
            .first()
        )

        if existing_slug:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subcategory slug '{slug}' already exists"
            )

        # --------------------------------------------------
        # Create subcategory
        # --------------------------------------------------

        subcategory = Subcategory(
            category_id=category_id,
            name=name,
            slug=slug,
            is_active=subcategory_data.is_active,
            display_order=index
        )

        db.add(subcategory)

        created_subcategories.append(subcategory)

    # ------------------------------------------------------
    # Commit all subcategories
    # ------------------------------------------------------

    db.commit()

    # ------------------------------------------------------
    # Refresh objects
    # ------------------------------------------------------

    for subcategory in created_subcategories:

        db.refresh(subcategory)

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 201,
        "message": "Subcategories created successfully",
        "count": len(created_subcategories),
        "subcategories": created_subcategories
    }


# ==========================================================
# GET ALL SUBCATEGORIES
# Active + Inactive
# ==========================================================

@router.get("/")
def get_all_subcategories(
    db: Session = Depends(get_db)
):

    subcategories = (
        db.query(Subcategory)
        .order_by(
            Subcategory.display_order.asc(),
            Subcategory.id.asc()
        )
        .all()
    )

    # ------------------------------------------------------
    # No subcategories
    # ------------------------------------------------------

    if not subcategories:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subcategories found"
        )

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "All subcategories fetched successfully",
        "count": len(subcategories),
        "subcategories": subcategories
    }


# ==========================================================
# GET ACTIVE SUBCATEGORIES ONLY
# ==========================================================

@router.get("/active")
def get_active_subcategories(
    db: Session = Depends(get_db)
):

    subcategories = (
        db.query(Subcategory)
        .filter(
            Subcategory.is_active.is_(True)
        )
        .order_by(
            Subcategory.display_order.asc(),
            Subcategory.id.asc()
        )
        .all()
    )

    # ------------------------------------------------------
    # No active subcategories
    # ------------------------------------------------------

    if not subcategories:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subcategories found"
        )

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "Active subcategories fetched successfully",
        "count": len(subcategories),
        "subcategories": subcategories
    }


# ==========================================================
# GET SUBCATEGORIES BY PARENT CATEGORY
# Active + Inactive
# ==========================================================

@router.get("/category/{category_id}")
def get_subcategories_by_category(
    category_id: int,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # Check parent category
    # ------------------------------------------------------

    parent_category = (
        db.query(Category)
        .filter(
            Category.id == category_id
        )
        .first()
    )

    if not parent_category:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent category not found"
        )

    # ------------------------------------------------------
    # Get subcategories
    # ------------------------------------------------------

    subcategories = (
        db.query(Subcategory)
        .filter(
            Subcategory.category_id == category_id
        )
        .order_by(
            Subcategory.display_order.asc(),
            Subcategory.id.asc()
        )
        .all()
    )

    if not subcategories:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subcategories found for this category"
        )

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "Subcategories fetched successfully",
        "category_id": category_id,
        "category_name": parent_category.name,
        "count": len(subcategories),
        "subcategories": subcategories
    }


# ==========================================================
# GET ACTIVE SUBCATEGORIES BY PARENT CATEGORY
# ==========================================================

@router.get("/category/{category_id}/active")
def get_active_subcategories_by_category(
    category_id: int,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # Check parent category
    # ------------------------------------------------------

    parent_category = (
        db.query(Category)
        .filter(
            Category.id == category_id
        )
        .first()
    )

    if not parent_category:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent category not found"
        )

    # ------------------------------------------------------
    # Get active subcategories
    # ------------------------------------------------------

    subcategories = (
        db.query(Subcategory)
        .filter(
            Subcategory.category_id == category_id,
            Subcategory.is_active.is_(True)
        )
        .order_by(
            Subcategory.display_order.asc(),
            Subcategory.id.asc()
        )
        .all()
    )

    if not subcategories:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subcategories found for this category"
        )

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "Active subcategories fetched successfully",
        "category_id": category_id,
        "category_name": parent_category.name,
        "count": len(subcategories),
        "subcategories": subcategories
    }


# ==========================================================
# GET SUBCATEGORY BY ID
# ==========================================================

@router.get("/{subcategory_id}")
def get_subcategory_by_id(
    subcategory_id: int,
    db: Session = Depends(get_db)
):

    subcategory = (
        db.query(Subcategory)
        .filter(
            Subcategory.id == subcategory_id
        )
        .first()
    )

    # ------------------------------------------------------
    # Subcategory not found
    # ------------------------------------------------------

    if not subcategory:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subcategory not found"
        )

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "Subcategory fetched successfully",
        "subcategory": subcategory
    }


# ==========================================================
# UPDATE SUBCATEGORY
# ==========================================================

@router.put("/{subcategory_id}")
def update_subcategory(
    subcategory_id: int,
    data: SubcategoryUpdate,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # Get subcategory
    # ------------------------------------------------------

    subcategory = (
        db.query(Subcategory)
        .filter(
            Subcategory.id == subcategory_id
        )
        .first()
    )

    # ------------------------------------------------------
    # Subcategory not found
    # ------------------------------------------------------

    if not subcategory:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subcategory not found"
        )

    # ======================================================
    # UPDATE PARENT CATEGORY
    # ======================================================

    if data.category_id is not None:

        parent_category = (
            db.query(Category)
            .filter(
                Category.id == data.category_id
            )
            .first()
        )

        if not parent_category:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )

        subcategory.category_id = data.category_id

    # ======================================================
    # UPDATE NAME
    # ======================================================

    if data.name is not None:

        name = data.name.strip()

        if not name:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subcategory name cannot be empty"
            )

        # --------------------------------------------------
        # Check duplicate name under same category
        # --------------------------------------------------

        existing_subcategory = (
            db.query(Subcategory)
            .filter(
                Subcategory.category_id == subcategory.category_id,
                Subcategory.name.ilike(name),
                Subcategory.id != subcategory_id
            )
            .first()
        )

        if existing_subcategory:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subcategory '{name}' already exists"
            )

        # --------------------------------------------------
        # Update name
        # --------------------------------------------------

        subcategory.name = name

        # --------------------------------------------------
        # Generate new slug
        # --------------------------------------------------

        slug = re.sub(
            r"[^a-z0-9]+",
            "-",
            name.lower()
        ).strip("-")

        if not slug:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subcategory name '{name}'"
            )

        # --------------------------------------------------
        # Check duplicate slug
        # --------------------------------------------------

        existing_slug = (
            db.query(Subcategory)
            .filter(
                Subcategory.slug == slug,
                Subcategory.id != subcategory_id
            )
            .first()
        )

        if existing_slug:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subcategory slug '{slug}' already exists"
            )

        # --------------------------------------------------
        # Update slug
        # --------------------------------------------------

        subcategory.slug = slug

    # ======================================================
    # UPDATE DESCRIPTION
    # ======================================================

    if data.description is not None:

        subcategory.description = data.description

    # ======================================================
    # UPDATE IMAGE
    # ======================================================

    if data.image is not None:

        subcategory.image = data.image

    # ======================================================
    # UPDATE ACTIVE STATUS
    # ======================================================

    if data.is_active is not None:

        subcategory.is_active = data.is_active

    # ======================================================
    # UPDATE DISPLAY ORDER
    # ======================================================

    if data.display_order is not None:

        subcategory.display_order = data.display_order

    # ------------------------------------------------------
    # Save changes
    # ------------------------------------------------------

    db.commit()

    # ------------------------------------------------------
    # Refresh object
    # ------------------------------------------------------

    db.refresh(subcategory)

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "Subcategory updated successfully",
        "subcategory": subcategory
    }


# ==========================================================
# DELETE SUBCATEGORY
# ==========================================================

@router.delete("/{subcategory_id}")
def delete_subcategory(
    subcategory_id: int,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # Get subcategory
    # ------------------------------------------------------

    subcategory = (
        db.query(Subcategory)
        .filter(
            Subcategory.id == subcategory_id
        )
        .first()
    )

    # ------------------------------------------------------
    # Subcategory not found
    # ------------------------------------------------------

    if not subcategory:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subcategory not found"
        )

    # ------------------------------------------------------
    # Delete subcategory
    # ------------------------------------------------------

    db.delete(subcategory)

    db.commit()

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "Subcategory deleted successfully",
        "subcategory_id": subcategory_id
    }