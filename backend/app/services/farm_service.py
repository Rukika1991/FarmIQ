from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Farm, Farmer
from app.schemas.farm import FarmCreate, FarmUpdate


def create_farm(db: Session, farm_data: FarmCreate):
    farmer = (
        db.query(Farmer)
        .filter(Farmer.id == farm_data.farmer_id)
        .first()
    )

    if not farmer:
        raise HTTPException(
            status_code=404,
            detail="Farmer not found.",
        )

    farm = Farm(
        farmer_id=farm_data.farmer_id,
        name=farm_data.name,
        district=farm_data.district,
        sector=farm_data.sector,
        village=farm_data.village,
        latitude=farm_data.latitude,
        longitude=farm_data.longitude,
    )

    try:
        db.add(farm)
        db.commit()
        db.refresh(farm)
        return farm

    except Exception:
        db.rollback()
        raise


def get_farms(db: Session):
    return db.query(Farm).order_by(Farm.id).all()


def get_farm(db: Session, farm_id: int):
    farm = (
        db.query(Farm)
        .filter(Farm.id == farm_id)
        .first()
    )

    if not farm:
        raise HTTPException(
            status_code=404,
            detail="Farm not found.",
        )

    return farm


def update_farm(
    db: Session,
    farm_id: int,
    farm_data: FarmUpdate,
):
    farm = get_farm(db, farm_id)

    update_data = farm_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(farm, field, value)

    try:
        db.commit()
        db.refresh(farm)
        return farm

    except Exception:
        db.rollback()
        raise


def delete_farm(db: Session, farm_id: int):
    farm = get_farm(db, farm_id)

    try:
        db.delete(farm)
        db.commit()

        return {
            "message": "Farm deleted successfully.",
            "farm_id": farm_id,
        }

    except Exception:
        db.rollback()
        raise
