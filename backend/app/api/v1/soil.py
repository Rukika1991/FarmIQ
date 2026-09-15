from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.soil import (
    SoilProfileCreate,
    SoilProfileUpdate,
    SoilProfileResponse,
)
from app.services.soil_service import (
    create_soil_profile,
    get_soil_profiles,
    get_soil_profile,
    get_active_soil_profile,
    update_soil_profile,
    delete_soil_profile,
)

router = APIRouter(
    prefix="/soil-profiles",
    tags=["Soil Profiles"],
)


@router.post(
    "",
    response_model=SoilProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_soil_profile_endpoint(
    soil_data: SoilProfileCreate,
    db: Session = Depends(get_db),
):
    return create_soil_profile(db, soil_data)


@router.get(
    "",
    response_model=list[SoilProfileResponse],
)
def get_soil_profiles_endpoint(
    field_id: int | None = None,
    db: Session = Depends(get_db),
):
    return get_soil_profiles(db, field_id)


@router.get(
    "/active/{field_id}",
    response_model=SoilProfileResponse | None,
)
def get_active_soil_profile_endpoint(
    field_id: int,
    db: Session = Depends(get_db),
):
    return get_active_soil_profile(db, field_id)


@router.get(
    "/{soil_profile_id}",
    response_model=SoilProfileResponse,
)
def get_soil_profile_endpoint(
    soil_profile_id: int,
    db: Session = Depends(get_db),
):
    return get_soil_profile(db, soil_profile_id)


@router.put(
    "/{soil_profile_id}",
    response_model=SoilProfileResponse,
)
def update_soil_profile_endpoint(
    soil_profile_id: int,
    soil_data: SoilProfileUpdate,
    db: Session = Depends(get_db),
):
    return update_soil_profile(
        db,
        soil_profile_id,
        soil_data,
    )


@router.delete(
    "/{soil_profile_id}",
)
def delete_soil_profile_endpoint(
    soil_profile_id: int,
    db: Session = Depends(get_db),
):
    return delete_soil_profile(
        db,
        soil_profile_id,
    )
