from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Field, Farm
from app.schemas.field import FieldCreate, FieldUpdate


def create_field(db: Session, field_data: FieldCreate):
    # Check that the farm exists
    farm = (
        db.query(Farm)
        .filter(Farm.id == field_data.farm_id)
        .first()
    )

    if not farm:
        raise HTTPException(
            status_code=404,
            detail="Farm not found.",
        )

    field = Field(
        farm_id=field_data.farm_id,
        name=field_data.name,
        area_hectares=field_data.area_hectares,
        latitude=field_data.latitude,
        longitude=field_data.longitude,
    )

    try:
        db.add(field)
        db.commit()
        db.refresh(field)

        return field

    except Exception:
        db.rollback()
        raise


def get_fields(db: Session):
    return (
        db.query(Field)
        .order_by(Field.id)
        .all()
    )


def get_field(db: Session, field_id: int):
    field = (
        db.query(Field)
        .filter(Field.id == field_id)
        .first()
    )

    if not field:
        raise HTTPException(
            status_code=404,
            detail="Field not found.",
        )

    return field


def update_field(
    db: Session,
    field_id: int,
    field_data: FieldUpdate,
):
    field = get_field(db, field_id)

    update_data = field_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(field, key, value)

    try:
        db.commit()
        db.refresh(field)

        return field

    except Exception:
        db.rollback()
        raise


def delete_field(db: Session, field_id: int):
    field = get_field(db, field_id)

    try:
        db.delete(field)
        db.commit()

        return {
            "message": "Field deleted successfully.",
            "field_id": field_id,
        }

    except Exception:
        db.rollback()
        raise
