from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.unit import Unit
from app.schemas.unit import (
    UnitCreate,
    UnitResponse,
    UnitUpdate,
)

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


# GET ALL UNITS
@router.get(
    "",
    response_model=list[UnitResponse]
)
def get_units(
    db: Session = Depends(get_db)
):

    units = (
        db.query(Unit)
        .order_by(Unit.display_order.asc(), Unit.id.asc())
        .all()
    )

    return units


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