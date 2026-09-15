from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import Field, SoilProfile
from app.schemas.soil import SoilProfileCreate, SoilProfileUpdate


def create_soil_profile(
    db: Session,
    soil_data: SoilProfileCreate,
):
    # ---------------------------------------------------------
    # 1. Check that the field exists
    # ---------------------------------------------------------
    field = (
        db.query(Field)
        .filter(Field.id == soil_data.field_id)
        .first()
    )

    if not field:
        raise HTTPException(
            status_code=404,
            detail="Field not found.",
        )

    # ---------------------------------------------------------
    # 2. Laboratory results have highest priority
    # ---------------------------------------------------------
    if soil_data.source == "LABORATORY":
        existing_active_profiles = (
            db.query(SoilProfile)
            .filter(
                SoilProfile.field_id == soil_data.field_id,
                SoilProfile.is_active.is_(True),
            )
            .all()
        )

        # Deactivate ALL previous active profiles.
        # They remain in the database as historical records.
        for profile in existing_active_profiles:
            profile.is_active = False

        # Laboratory results always have HIGH confidence.
        soil_data.confidence = "HIGH"
        soil_data.is_active = True

    # ---------------------------------------------------------
    # 3. Location estimate
    # ---------------------------------------------------------
    elif soil_data.source == "LOCATION_ESTIMATE":
        existing_lab = (
            db.query(SoilProfile)
            .filter(
                SoilProfile.field_id == soil_data.field_id,
                SoilProfile.source == "LABORATORY",
                SoilProfile.is_active.is_(True),
            )
            .first()
        )

        # Never allow an estimate to replace an active
        # laboratory result.
        if existing_lab:
            soil_data.is_active = False
            soil_data.confidence = "MEDIUM"

    # ---------------------------------------------------------
    # 4. Create soil profile
    # ---------------------------------------------------------
    profile = SoilProfile(
        field_id=soil_data.field_id,
        source=soil_data.source,
        ph=soil_data.ph,
        nitrogen=soil_data.nitrogen,
        phosphorus=soil_data.phosphorus,
        potassium=soil_data.potassium,
        organic_carbon=soil_data.organic_carbon,
        texture=soil_data.texture,
        soil_depth_cm=soil_data.soil_depth_cm,
        drainage=soil_data.drainage,
        confidence=soil_data.confidence,
        test_date=soil_data.test_date,
        is_active=soil_data.is_active,
        notes=soil_data.notes,
    )

    try:
        db.add(profile)
        db.commit()
        db.refresh(profile)

        return profile

    except Exception:
        db.rollback()
        raise


def get_soil_profiles(
    db: Session,
    field_id: int | None = None,
):
    query = db.query(SoilProfile)

    if field_id is not None:
        query = query.filter(
            SoilProfile.field_id == field_id
        )

    return (
        query
        .order_by(SoilProfile.id)
        .all()
    )


def get_soil_profile(
    db: Session,
    soil_profile_id: int,
):
    profile = (
        db.query(SoilProfile)
        .filter(SoilProfile.id == soil_profile_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Soil profile not found.",
        )

    return profile


def get_active_soil_profile(
    db: Session,
    field_id: int,
):
    """
    Return the soil profile FarmIQ should currently use.

    Priority:
        1. Active laboratory profile
        2. Active location estimate
    """

    laboratory = (
        db.query(SoilProfile)
        .filter(
            SoilProfile.field_id == field_id,
            SoilProfile.source == "LABORATORY",
            SoilProfile.is_active.is_(True),
        )
        .order_by(
            SoilProfile.test_date.desc().nullslast(),
            SoilProfile.id.desc(),
        )
        .first()
    )

    if laboratory:
        return laboratory

    estimate = (
        db.query(SoilProfile)
        .filter(
            SoilProfile.field_id == field_id,
            SoilProfile.source == "LOCATION_ESTIMATE",
            SoilProfile.is_active.is_(True),
        )
        .order_by(
            SoilProfile.id.desc()
        )
        .first()
    )

    return estimate


def update_soil_profile(
    db: Session,
    soil_profile_id: int,
    soil_data: SoilProfileUpdate,
):
    profile = get_soil_profile(
        db,
        soil_profile_id,
    )

    update_data = soil_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(profile, key, value)

    try:
        db.commit()
        db.refresh(profile)

        return profile

    except Exception:
        db.rollback()
        raise


def delete_soil_profile(
    db: Session,
    soil_profile_id: int,
):
    profile = get_soil_profile(
        db,
        soil_profile_id,
    )

    try:
        db.delete(profile)
        db.commit()

        return {
            "message": "Soil profile deleted successfully.",
            "soil_profile_id": soil_profile_id,
        }

    except Exception:
        db.rollback()
        raise