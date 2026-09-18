# from fastapi import APIRouter,Depends,HTTPException,status
# from sqlalchemy.orm import Session

# from app.database import get_db
# from app.models.unit import Unit
# from app.schemas.unit import (
#     UnitCreate,
#     UnitResponse,
#     UnitUpdate,
# )

# router = APIRouter(
#     prefix = "/units",
#     tags = ["Units"]
# )

# #create unit
# @router.post(
#     "",
#     response_model=UnitResponse,
#     status_code=status.HTTP_201_CREATED
# )
# def create_unit(
#     data: UnitCreate,
#     db: Session = Depends(get_db)
# ):

#     existing_unit = (
#         db.query(Unit)
#         .filter(
#             (Unit.name == data.name) |
#             (Unit.short_name == data.short_name)
#         )
#         .first()
#     )

#     if existing_unit:
#         raise HTTPException(
#             status_code=400,
#             detail="Unit name or short name already exists"
#         )

#     unit = Unit(
#         name=data.name,
#         short_name=data.short_name,
#         description=data.description,
#         is_active=data.is_active,
#         display_order=data.display_order
#     )

#     db.add(unit)
#     db.commit()
#     db.refresh(unit)

#     return unit


# # GET ALL UNITS
# @router.get(
#     "",
#     response_model=list[UnitResponse]
# )
# def get_units(
#     db: Session = Depends(get_db)
# ):

#     units = (
#         db.query(Unit)
#         .order_by(Unit.display_order.asc(), Unit.id.asc())
#         .all()
#     )

#     return units


# # GET SINGLE UNIT
# @router.get(
#     "/{unit_id}",
#     response_model=UnitResponse
# )
# def get_unit(
#     unit_id: int,
#     db: Session = Depends(get_db)
# ):

#     unit = (
#         db.query(Unit)
#         .filter(Unit.id == unit_id)
#         .first()
#     )

#     if not unit:
#         raise HTTPException(
#             status_code=404,
#             detail="Unit not found"
#         )

#     return unit


# # UPDATE UNIT
# @router.put("/{unit_id}", response_model=UnitResponse)
# def update_unit(
#     unit_id: int,
#     data: UnitUpdate,
#     db: Session = Depends(get_db)
# ):
#     unit = db.query(Unit).filter(Unit.id == unit_id).first()

#     if not unit:
#         raise HTTPException(
#             status_code=404,
#             detail="Unit not found"
#         )

#     if data.name is not None:
#         unit.name = data.name

#     if data.short_name is not None:
#         unit.short_name = data.short_name

#     if data.description is not None:
#         unit.description = data.description

#     if data.is_active is not None:
#         unit.is_active = data.is_active

#     if data.display_order is not None:
#         unit.display_order = data.display_order

#     db.commit()
#     db.refresh(unit)

#     return unit


# # DELETE UNIT
# @router.delete(
#     "/{unit_id}"
# )
# def delete_unit(
#     unit_id: int,
#     db: Session = Depends(get_db)
# ):

#     unit = (
#         db.query(Unit)
#         .filter(Unit.id == unit_id)
#         .first()
#     )

#     if not unit:
#         raise HTTPException(
#             status_code=404,
#             detail="Unit not found"
#         )

#     db.delete(unit)
#     db.commit()

#     return {
#         "message": "Unit deleted successfully"
#     }

from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.unit import Unit
from app.schemas.unit import (
    UnitCreate,
    UnitResponse,
    UnitUpdate,
)

from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.unit import Unit
from app.schemas.unit import UnitResponse

router = APIRouter(
    prefix = "/units",
    tags = ["Units"]
)

#create unit
@router.post(
    "",
    response_model=UnitResponse,
    status_code=status.HTTP_201_CREATED
)
def create_unit(
    data: UnitCreate,
    db: Session = Depends(get_db)
):

    existing_unit = (
        db.query(Unit)
        .filter(
            (Unit.name == data.name) |
            (Unit.short_name == data.short_name)
        )
        .first()
    )

    if existing_unit:
        raise HTTPException(
            status_code=400,
            detail="Unit name or short name already exists"
        )

    unit = Unit(
        name=data.name,
        short_name=data.short_name,
        description=data.description,
        is_active=data.is_active,
        display_order=data.display_order
    )

    db.add(unit)
    db.commit()
    db.refresh(unit)

    return unit


# ==========================================================
# GET ALL UNITS
# Pagination + Date Filter
# ==========================================================

@router.get(
    "",
    response_model=dict
)
def get_units(
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
        description="Number of units per page"
    ),
    db: Session = Depends(get_db)
):

    # ======================================================
    # DATE VALIDATION
    # ======================================================

    if start_date and end_date:

        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date cannot be greater than end_date"
            )

    # ======================================================
    # BASE QUERY
    # ======================================================

    units_query = db.query(Unit)

    # ======================================================
    # DATE FILTER
    # ======================================================

    if start_date or end_date:

        india_timezone = ZoneInfo("Asia/Kolkata")
        utc_timezone = ZoneInfo("UTC")

        if start_date is None:
            start_date = end_date

        if end_date is None:
            end_date = start_date

        # Start date - 00:00:00 IST
        start_india_datetime = datetime.combine(
            start_date,
            time.min
        ).replace(
            tzinfo=india_timezone
        )

        # End date inclusive
        # Next day 00:00:00 IST
        end_india_datetime = datetime.combine(
            end_date + timedelta(days=1),
            time.min
        ).replace(
            tzinfo=india_timezone
        )

        # Convert IST -> UTC
        start_utc_datetime = (
            start_india_datetime
            .astimezone(utc_timezone)
            .replace(tzinfo=None)
        )

        end_utc_datetime = (
            end_india_datetime
            .astimezone(utc_timezone)
            .replace(tzinfo=None)
        )

        units_query = units_query.filter(
            Unit.created_at >= start_utc_datetime,
            Unit.created_at < end_utc_datetime
        )

    # ======================================================
    # ORDERING
    # ======================================================

    units_query = units_query.order_by(
        Unit.display_order.asc(),
        Unit.id.asc()
    )

    # ======================================================
    # TOTAL COUNT
    # ======================================================

    total_units = units_query.count()

    if total_units == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No units found for the selected date range"
        )

    # ======================================================
    # PAGINATION
    # ======================================================

    offset = (page - 1) * limit

    units = (
        units_query
        .offset(offset)
        .limit(limit)
        .all()
    )

    if not units:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No units found for this page"
        )

    total_pages = (
        total_units + limit - 1
    ) // limit

    # ======================================================
    # CONVERT SQLALCHEMY OBJECT TO DICTIONARY
    # ======================================================

    unit_data = []

    for unit in units:

        unit_data.append({
            "id": unit.id,
            "name": unit.name,
            "short_name": unit.short_name,
            "description": unit.description,
            "is_active": unit.is_active,
            "display_order": unit.display_order,
            "created_at": unit.created_at,
            "updated_at": unit.updated_at
        })

    # ======================================================
    # RESPONSE
    # ======================================================

    return {
        "status_code": 200,
        "message": "Units fetched successfully",

        "filters": {
            "start_date": start_date,
            "end_date": end_date
        },

        "pagination": {
            "current_page": page,
            "per_page": limit,
            "total_units": total_units,
            "total_pages": total_pages,
            "has_next_page": page < total_pages,
            "has_previous_page": page > 1
        },

        "count": len(unit_data),

        "units": unit_data
    }


# GET SINGLE UNIT
@router.get(
    "/{unit_id}",
    response_model=UnitResponse
)
def get_unit(
    unit_id: int,
    db: Session = Depends(get_db)
):

    unit = (
        db.query(Unit)
        .filter(Unit.id == unit_id)
        .first()
    )

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found"
        )

    return unit


# UPDATE UNIT
@router.put("/{unit_id}", response_model=UnitResponse)
def update_unit(
    unit_id: int,
    data: UnitUpdate,
    db: Session = Depends(get_db)
):
    unit = db.query(Unit).filter(Unit.id == unit_id).first()

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found"
        )

    if data.name is not None:
        unit.name = data.name

    if data.short_name is not None:
        unit.short_name = data.short_name

    if data.description is not None:
        unit.description = data.description

    if data.is_active is not None:
        unit.is_active = data.is_active

    if data.display_order is not None:
        unit.display_order = data.display_order

    db.commit()
    db.refresh(unit)

    return unit


# DELETE UNIT
@router.delete(
    "/{unit_id}"
)
def delete_unit(
    unit_id: int,
    db: Session = Depends(get_db)
):

    unit = (
        db.query(Unit)
        .filter(Unit.id == unit_id)
        .first()
    )

    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found"
        )

    db.delete(unit)
    db.commit()

    return {
        "message": "Unit deleted successfully"
    }