from sqlalchemy.orm import Session

from app.models.models import Crop, CropSeason, Field
from app.schemas.crop_season import CropSeasonCreate, CropSeasonUpdate


class CropSeasonService:

    @staticmethod
    def _validate_area(
        area_hectares,
        field: Field,
    ) -> None:
        if area_hectares > field.area_hectares:
            raise ValueError(
                f"Crop season area ({area_hectares} ha) "
                f"cannot exceed field area ({field.area_hectares} ha)."
            )

    # -------------------------------------------------------------
    # Create
    # -------------------------------------------------------------
    @staticmethod
    def create_crop_season(
        db: Session,
        data: CropSeasonCreate,
    ) -> CropSeason:

        field = (
            db.query(Field)
            .filter(Field.id == data.field_id)
            .first()
        )

        if not field:
            raise ValueError("Field not found.")

        crop = (
            db.query(Crop)
            .filter(Crop.id == data.crop_id)
            .first()
        )

        if not crop:
            raise ValueError("Crop not found.")

        CropSeasonService._validate_area(
            data.area_hectares,
            field,
        )

        crop_season = CropSeason(
            field_id=data.field_id,
            crop_id=data.crop_id,
            variety=data.variety,
            area_hectares=data.area_hectares,
            planting_date=data.planting_date,
            expected_harvest_date=data.expected_harvest_date,
            actual_harvest_date=data.actual_harvest_date,
            expected_yield_kg=data.expected_yield_kg,
            actual_yield_kg=data.actual_yield_kg,
            status=data.status,
            notes=data.notes,
        )

        db.add(crop_season)

        try:
            db.commit()
            db.refresh(crop_season)
        except Exception:
            db.rollback()
            raise

        return crop_season

    # -------------------------------------------------------------
    # Get all
    # -------------------------------------------------------------
    @staticmethod
    def get_crop_seasons(
        db: Session,
        field_id: int | None = None,
        crop_id: int | None = None,
    ) -> list[CropSeason]:

        query = db.query(CropSeason)

        if field_id is not None:
            query = query.filter(
                CropSeason.field_id == field_id
            )

        if crop_id is not None:
            query = query.filter(
                CropSeason.crop_id == crop_id
            )

        return query.order_by(
            CropSeason.id.desc()
        ).all()

    # -------------------------------------------------------------
    # Get one
    # -------------------------------------------------------------
    @staticmethod
    def get_crop_season(
        db: Session,
        crop_season_id: int,
    ) -> CropSeason:

        crop_season = (
            db.query(CropSeason)
            .filter(CropSeason.id == crop_season_id)
            .first()
        )

        if not crop_season:
            raise ValueError("Crop season not found.")

        return crop_season

    # -------------------------------------------------------------
    # Update
    # -------------------------------------------------------------
    @staticmethod
    def update_crop_season(
        db: Session,
        crop_season_id: int,
        data: CropSeasonUpdate,
    ) -> CropSeason:

        crop_season = (
            db.query(CropSeason)
            .filter(CropSeason.id == crop_season_id)
            .first()
        )

        if not crop_season:
            raise ValueError("Crop season not found.")

        # ---------------------------------------------------------
        # Determine the field that will be used after the update
        # ---------------------------------------------------------
        target_field_id = (
            data.field_id
            if data.field_id is not None
            else crop_season.field_id
        )

        field = (
            db.query(Field)
            .filter(Field.id == target_field_id)
            .first()
        )

        if not field:
            raise ValueError("Field not found.")

        # ---------------------------------------------------------
        # Validate crop if changing it
        # ---------------------------------------------------------
        if data.crop_id is not None:

            crop = (
                db.query(Crop)
                .filter(Crop.id == data.crop_id)
                .first()
            )

            if not crop:
                raise ValueError("Crop not found.")

        # ---------------------------------------------------------
        # Determine the final area
        # ---------------------------------------------------------
        target_area = (
            data.area_hectares
            if data.area_hectares is not None
            else crop_season.area_hectares
        )

        CropSeasonService._validate_area(
            target_area,
            field,
        )

        # ---------------------------------------------------------
        # Apply changes
        # ---------------------------------------------------------
        if data.field_id is not None:
            crop_season.field_id = data.field_id

        if data.crop_id is not None:
            crop_season.crop_id = data.crop_id

        if data.variety is not None:
            crop_season.variety = data.variety

        if data.area_hectares is not None:
            crop_season.area_hectares = data.area_hectares

        if data.planting_date is not None:
            crop_season.planting_date = data.planting_date

        if data.expected_harvest_date is not None:
            crop_season.expected_harvest_date = (
                data.expected_harvest_date
            )

        if data.actual_harvest_date is not None:
            crop_season.actual_harvest_date = (
                data.actual_harvest_date
            )

        if data.expected_yield_kg is not None:
            crop_season.expected_yield_kg = (
                data.expected_yield_kg
            )

        if data.actual_yield_kg is not None:
            crop_season.actual_yield_kg = (
                data.actual_yield_kg
            )

        if data.status is not None:
            crop_season.status = data.status

        if data.notes is not None:
            crop_season.notes = data.notes

        try:
            db.commit()
            db.refresh(crop_season)
        except Exception:
            db.rollback()
            raise

        return crop_season

    # -------------------------------------------------------------
    # Delete
    # -------------------------------------------------------------
    @staticmethod
    def delete_crop_season(
        db: Session,
        crop_season_id: int,
    ) -> dict:

        crop_season = (
            db.query(CropSeason)
            .filter(CropSeason.id == crop_season_id)
            .first()
        )

        if not crop_season:
            raise ValueError("Crop season not found.")

        db.delete(crop_season)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        return {
            "message": "Crop season deleted successfully.",
            "crop_season_id": crop_season_id,
        }
