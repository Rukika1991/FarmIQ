from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.crop_season import (
    CropSeasonCreate,
    CropSeasonResponse,
    CropSeasonUpdate,
)
from app.services.crop_season_service import CropSeasonService


router = APIRouter(
    prefix="/crop-seasons",
    tags=["Crop Seasons"],
)


# ============================================================
# CREATE CROP SEASON
# ============================================================

@router.post(
    "",
    response_model=CropSeasonResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_crop_season(
    data: CropSeasonCreate,
    db: Session = Depends(get_db),
):
    try:
        return CropSeasonService.create_crop_season(db, data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================================
# GET ALL CROP SEASONS
# ============================================================

@router.get(
    "",
    response_model=list[CropSeasonResponse],
)
def get_crop_seasons(
    field_id: int | None = Query(default=None),
    crop_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return CropSeasonService.get_crop_seasons(
        db,
        field_id=field_id,
        crop_id=crop_id,
    )


# ============================================================
# GET ONE CROP SEASON
# ============================================================

@router.get(
    "/{crop_season_id}",
    response_model=CropSeasonResponse,
)
def get_crop_season(
    crop_season_id: int,
    db: Session = Depends(get_db),
):
    try:
        return CropSeasonService.get_crop_season(
            db,
            crop_season_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ============================================================
# UPDATE CROP SEASON
# ============================================================

@router.put(
    "/{crop_season_id}",
    response_model=CropSeasonResponse,
)
def update_crop_season(
    crop_season_id: int,
    data: CropSeasonUpdate,
    db: Session = Depends(get_db),
):
    try:
        return CropSeasonService.update_crop_season(
            db,
            crop_season_id,
            data,
        )

    except ValueError as e:
        message = str(e)

        # Resource not found
        if (
            "not found" in message.lower()
            or "does not exist" in message.lower()
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            )

        # Business validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


# ============================================================
# DELETE CROP SEASON
# ============================================================

@router.delete(
    "/{crop_season_id}",
)
def delete_crop_season(
    crop_season_id: int,
    db: Session = Depends(get_db),
):
    try:
        return CropSeasonService.delete_crop_season(
            db,
            crop_season_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )