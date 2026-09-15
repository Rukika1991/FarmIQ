from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.farm import FarmCreate, FarmUpdate, FarmResponse
from app.services.farm_service import (
    create_farm,
    get_farms,
    get_farm,
    update_farm,
    delete_farm,
)

router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
)


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_farm_endpoint(
    farm_data: FarmCreate,
    db: Session = Depends(get_db),
):
    return create_farm(db, farm_data)


@router.get(
    "",
    response_model=list[FarmResponse],
)
def get_farms_endpoint(
    db: Session = Depends(get_db),
):
    return get_farms(db)


@router.get(
    "/{farm_id}",
    response_model=FarmResponse,
)
def get_farm_endpoint(
    farm_id: int,
    db: Session = Depends(get_db),
):
    return get_farm(db, farm_id)


@router.put(
    "/{farm_id}",
    response_model=FarmResponse,
)
def update_farm_endpoint(
    farm_id: int,
    farm_data: FarmUpdate,
    db: Session = Depends(get_db),
):
    return update_farm(db, farm_id, farm_data)


@router.delete(
    "/{farm_id}",
)
def delete_farm_endpoint(
    farm_id: int,
    db: Session = Depends(get_db),
):
    return delete_farm(db, farm_id)
