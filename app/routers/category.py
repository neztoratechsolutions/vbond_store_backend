# ==========================================================
# CATEGORY ROUTER
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
from app.models.category import Category

from app.schemas.category import (
    CategoryBulkCreate,
    CategoryUpdate
)


# ==========================================================
# ROUTER
# ==========================================================

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


# ==========================================================
# POST - BULK CREATE CATEGORIES
# ==========================================================

@router.post(
    "/bulk",
    status_code=status.HTTP_201_CREATED
)
def create_categories(
    data: CategoryBulkCreate,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # Check category list
    # ------------------------------------------------------

    if not data.categories:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one category is required"
        )

    created_categories = []

    # ------------------------------------------------------
    # Loop through categories
    # ------------------------------------------------------

    for index, category_data in enumerate(
        data.categories,
        start=1
    ):

        # --------------------------------------------------
        # Get category name
        # --------------------------------------------------

        name = category_data.name.strip()

        if not name:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category {index} name cannot be empty"
            )

        # --------------------------------------------------
        # Check duplicate category name
        # --------------------------------------------------

        existing_category = (
            db.query(Category)
            .filter(
                Category.name.ilike(name)
            )
            .first()
        )

        if existing_category:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{name}' already exists"
            )

        # --------------------------------------------------
        # Generate slug
        # --------------------------------------------------

        slug = re.sub(
            r"[^a-z0-9]+",
            "-",
            name.lower()
        ).strip("-")

        # --------------------------------------------------
        # Check generated slug
        # --------------------------------------------------

        if not slug:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category name '{name}'"
            )

        # --------------------------------------------------
        # Check duplicate slug
        # --------------------------------------------------

        existing_slug = (
            db.query(Category)
            .filter(
                Category.slug == slug
            )
            .first()
        )

        if existing_slug:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category slug '{slug}' already exists"
            )

        # --------------------------------------------------
        # Create category
        # --------------------------------------------------

        category = Category(
            name=name,
            slug=slug,
            is_active=category_data.is_active,
            display_order=index
        )

        db.add(category)

        created_categories.append(category)

    # ------------------------------------------------------
    # Commit all categories
    # ------------------------------------------------------

    db.commit()

    # ------------------------------------------------------
    # Refresh objects
    # ------------------------------------------------------

    for category in created_categories:

        db.refresh(category)

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 201,
        "message": "Categories created successfully",
        "count": len(created_categories),
        "categories": created_categories
    }


# ==========================================================
# GET ALL CATEGORIES
# Active + Inactive
# ==========================================================

@router.get("/")
def get_all_categories(
    db: Session = Depends(get_db)
):

    categories = (
        db.query(Category)
        .order_by(
            Category.display_order.asc(),
            Category.id.asc()
        )
        .all()
    )

    # ------------------------------------------------------
    # No categories
    # ------------------------------------------------------

    if not categories:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No categories found"
        )

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "All categories fetched successfully",
        "count": len(categories),
        "categories": categories
    }


# ==========================================================
# GET ACTIVE CATEGORIES ONLY
# is_active = True
# ==========================================================

@router.get("/active")
def get_active_categories(
    db: Session = Depends(get_db)
):

    categories = (
        db.query(Category)
        .filter(
            Category.is_active.is_(True)
        )
        .order_by(
            Category.display_order.asc(),
            Category.id.asc()
        )
        .all()
    )

    # ------------------------------------------------------
    # No active categories
    # ------------------------------------------------------

    if not categories:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active categories found"
        )

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "Active categories fetched successfully",
        "count": len(categories),
        "categories": categories
    }


# ==========================================================
# GET CATEGORY BY ID
# ==========================================================

@router.get("/{category_id}")
def get_category_by_id(
    category_id: int,
    db: Session = Depends(get_db)
):

    category = (
        db.query(Category)
        .filter(
            Category.id == category_id
        )
        .first()
    )

    # ------------------------------------------------------
    # Category not found
    # ------------------------------------------------------

    if not category:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "Category fetched successfully",
        "category": category
    }


# ==========================================================
# UPDATE CATEGORY
# ==========================================================

@router.put("/{category_id}")
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # Get category
    # ------------------------------------------------------

    category = (
        db.query(Category)
        .filter(
            Category.id == category_id
        )
        .first()
    )

    # ------------------------------------------------------
    # Category not found
    # ------------------------------------------------------

    if not category:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # ======================================================
    # UPDATE NAME
    # ======================================================

    if data.name is not None:

        name = data.name.strip()

        # --------------------------------------------------
        # Empty name
        # --------------------------------------------------

        if not name:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name cannot be empty"
            )

        # --------------------------------------------------
        # Check duplicate name
        # --------------------------------------------------

        existing_category = (
            db.query(Category)
            .filter(
                Category.name.ilike(name),
                Category.id != category_id
            )
            .first()
        )

        if existing_category:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{name}' already exists"
            )

        # --------------------------------------------------
        # Update name
        # --------------------------------------------------

        category.name = name

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
                detail=f"Invalid category name '{name}'"
            )

        # --------------------------------------------------
        # Check duplicate slug
        # --------------------------------------------------

        existing_slug = (
            db.query(Category)
            .filter(
                Category.slug == slug,
                Category.id != category_id
            )
            .first()
        )

        if existing_slug:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category slug '{slug}' already exists"
            )

        # --------------------------------------------------
        # Update slug
        # --------------------------------------------------

        category.slug = slug

    # ======================================================
    # UPDATE DESCRIPTION
    # ======================================================

    if data.description is not None:

        category.description = data.description

    # ======================================================
    # UPDATE IMAGE
    # ======================================================

    if data.image is not None:

        category.image = data.image

    # ======================================================
    # UPDATE ACTIVE STATUS
    # ======================================================

    if data.is_active is not None:

        category.is_active = data.is_active

    # ======================================================
    # UPDATE DISPLAY ORDER
    # ======================================================

    if data.display_order is not None:

        category.display_order = data.display_order

    # ------------------------------------------------------
    # Save changes
    # ------------------------------------------------------

    db.commit()

    # ------------------------------------------------------
    # Refresh category
    # ------------------------------------------------------

    db.refresh(category)

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "Category updated successfully",
        "category": category
    }


# ==========================================================
# DELETE CATEGORY
# ==========================================================

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # Get category
    # ------------------------------------------------------

    category = (
        db.query(Category)
        .filter(
            Category.id == category_id
        )
        .first()
    )

    # ------------------------------------------------------
    # Category not found
    # ------------------------------------------------------

    if not category:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # ------------------------------------------------------
    # Delete category
    # ------------------------------------------------------

    db.delete(category)

    db.commit()

    # ------------------------------------------------------
    # Response
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "Category deleted successfully",
        "category_id": category_id
    }