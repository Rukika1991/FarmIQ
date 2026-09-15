from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.crop import CropCreate, CropUpdate, CropResponse
from app.services.crop_service import (
    create_crop,
    get_crops,
    get_crop,
    update_crop,
    delete_crop,
)

router = APIRouter(
    prefix="/crops",
    tags=["Crops"],
)


@router.post(
    "",
    response_model=CropResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_crop_endpoint(
    crop_data: CropCreate,
    db: Session = Depends(get_db),
):
    return create_crop(db, crop_data)


@router.get(
    "",
    response_model=list[CropResponse],
)
def get_crops_endpoint(
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    return get_crops(db, active_only)


@router.get(
    "/{crop_id}",
    response_model=CropResponse,
)
def get_crop_endpoint(
    crop_id: int,
    db: Session = Depends(get_db),
):
    return get_crop(db, crop_id)


@router.put(
    "/{crop_id}",
    response_model=CropResponse,
)
def update_crop_endpoint(
    crop_id: int,
    crop_data: CropUpdate,
    db: Session = Depends(get_db),
):
    return update_crop(
        db,
        crop_id,
        crop_data,
    )


@router.delete(
    "/{crop_id}",
)
def delete_crop_endpoint(
    crop_id: int,
    db: Session = Depends(get_db),
):
    return delete_crop(
        db,
        crop_id,
    )
