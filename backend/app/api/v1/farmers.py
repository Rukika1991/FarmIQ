from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.farmer import FarmerCreate, FarmerResponse
from app.services.farmer_service import (
    create_farmer,
    get_farmer,
    get_farmers,
)


router = APIRouter(
    prefix="/farmers",
    tags=["Farmers"],
)


@router.post(
    "",
    response_model=FarmerResponse,
    status_code=201,
)
def create_farmer_endpoint(
    farmer_data: FarmerCreate,
    db: Session = Depends(get_db),
):
    try:
        farmer = create_farmer(db, farmer_data)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "id": farmer.id,
        "full_name": farmer.user.full_name,
        "email": farmer.user.email,
        "phone": farmer.phone,
        "role": farmer.user.role,
        "is_active": farmer.user.is_active,
    }


@router.get(
    "",
    response_model=list[FarmerResponse],
)
def list_farmers(
    db: Session = Depends(get_db),
):
    farmers = get_farmers(db)

    return [
        {
            "id": farmer.id,
            "full_name": farmer.user.full_name,
            "email": farmer.user.email,
            "phone": farmer.phone,
            "role": farmer.user.role,
            "is_active": farmer.user.is_active,
        }
        for farmer in farmers
    ]


@router.get(
    "/{farmer_id}",
    response_model=FarmerResponse,
)
def get_farmer_endpoint(
    farmer_id: int,
    db: Session = Depends(get_db),
):
    farmer = get_farmer(db, farmer_id)

    if not farmer:
        raise HTTPException(
            status_code=404,
            detail="Farmer not found.",
        )

    return {
        "id": farmer.id,
        "full_name": farmer.user.full_name,
        "email": farmer.user.email,
        "phone": farmer.phone,
        "role": farmer.user.role,
        "is_active": farmer.user.is_active,
    }
