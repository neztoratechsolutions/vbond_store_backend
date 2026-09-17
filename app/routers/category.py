# ==========================================================
# CATEGORY ROUTER
# ==========================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from fastapi import Query
from sqlalchemy.orm import Session
from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import Query

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
# Pagination + Date Filter
# ==========================================================

@router.get("/")
def get_all_categories(
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
        description="Number of categories per page"
    ),
    db: Session = Depends(get_db)
):

    # ------------------------------------------------------
    # VALIDATE DATE RANGE
    # ------------------------------------------------------

    if start_date and end_date:
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date cannot be greater than end_date"
            )

    # ------------------------------------------------------
    # CATEGORY QUERY
    # ------------------------------------------------------

    categories_query = db.query(Category)

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

        # end_date + 1 day makes the end date inclusive
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

        categories_query = categories_query.filter(
            Category.created_at >= start_utc_datetime,
            Category.created_at < end_utc_datetime
        )

    # ------------------------------------------------------
    # ORDER BY
    # ------------------------------------------------------

    categories_query = categories_query.order_by(
        Category.display_order.asc(),
        Category.id.asc()
    )

    # ------------------------------------------------------
    # TOTAL COUNT
    # ------------------------------------------------------

    total_categories = categories_query.count()

    if total_categories == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No categories found for the selected date range"
        )

    # ------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------

    offset = (page - 1) * limit

    categories = (
        categories_query
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No categories found for this page"
        )

    total_pages = (
        total_categories + limit - 1
    ) // limit

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return {
        "status_code": 200,
        "message": "All categories fetched successfully",

        "filters": {
            "start_date": start_date,
            "end_date": end_date
        },

        "pagination": {
            "current_page": page,
            "per_page": limit,
            "total_categories": total_categories,
            "total_pages": total_pages,
            "has_next_page": page < total_pages,
            "has_previous_page": page > 1
        },

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