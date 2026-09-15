from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Crop
from app.schemas.crop import CropCreate, CropUpdate


def create_crop(
    db: Session,
    crop_data: CropCreate,
):
    # ---------------------------------------------------------
    # 1. Prevent duplicate crop names
    # ---------------------------------------------------------
    existing_crop = (
        db.query(Crop)
        .filter(Crop.name.ilike(crop_data.name.strip()))
        .first()
    )

    if existing_crop:
        raise HTTPException(
            status_code=409,
            detail="A crop with this name already exists.",
        )

    # ---------------------------------------------------------
    # 2. Create crop
    # ---------------------------------------------------------
    crop = Crop(
        name=crop_data.name.strip(),
        scientific_name=(
            crop_data.scientific_name.strip()
            if crop_data.scientific_name
            else None
        ),
        description=crop_data.description,
        is_active=crop_data.is_active,
    )

    try:
        db.add(crop)
        db.commit()
        db.refresh(crop)

        return crop

    except Exception:
        db.rollback()
        raise


def get_crops(
    db: Session,
    active_only: bool = False,
):
    query = db.query(Crop)

    if active_only:
        query = query.filter(
            Crop.is_active.is_(True)
        )

    return (
        query
        .order_by(Crop.name)
        .all()
    )


def get_crop(
    db: Session,
    crop_id: int,
):
    crop = (
        db.query(Crop)
        .filter(Crop.id == crop_id)
        .first()
    )

    if not crop:
        raise HTTPException(
            status_code=404,
            detail="Crop not found.",
        )

    return crop


def update_crop(
    db: Session,
    crop_id: int,
    crop_data: CropUpdate,
):
    crop = get_crop(db, crop_id)

    update_data = crop_data.model_dump(
        exclude_unset=True
    )

    # ---------------------------------------------------------
    # Check duplicate name during update
    # ---------------------------------------------------------
    if "name" in update_data:
        new_name = update_data["name"].strip()

        existing_crop = (
            db.query(Crop)
            .filter(
                Crop.name.ilike(new_name),
                Crop.id != crop_id,
            )
            .first()
        )

        if existing_crop:
            raise HTTPException(
                status_code=409,
                detail="A crop with this name already exists.",
            )

        update_data["name"] = new_name

    for key, value in update_data.items():
        setattr(crop, key, value)

    try:
        db.commit()
        db.refresh(crop)

        return crop

    except Exception:
        db.rollback()
        raise


def delete_crop(
    db: Session,
    crop_id: int,
):
    crop = get_crop(db, crop_id)

    try:
        db.delete(crop)
        db.commit()

        return {
            "message": "Crop deleted successfully.",
            "crop_id": crop_id,
        }

    except Exception:
        db.rollback()
        raise
