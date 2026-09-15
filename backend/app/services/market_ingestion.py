from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market import Market, MarketPrice
from app.models.models import Crop


class MarketIngestionService:
    """
    Service responsible for ingesting market price observations
    from different sources into the FarmIQ database.
    """

    SUPPORTED_UNITS = {
        "KG",
        "TONNE",
        "BAG",
        "LITRE",
        "PIECE",
        "OTHER",
    }

    MAX_SOURCE_LENGTH = 150
    MAX_SOURCE_REFERENCE_LENGTH = 500
    MAX_CURRENCY_LENGTH = 10
    MAX_UNIT_LENGTH = 30

    def __init__(self, db: Session):
        self.db = db

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_market(self, market_id: int) -> Market:
        market = self.db.scalar(
            select(Market).where(Market.id == market_id)
        )

        if market is None:
            raise ValueError(
                f"Market with ID {market_id} was not found."
            )

        if not market.is_active:
            raise ValueError(
                f"Market '{market.name}' is inactive."
            )

        return market

    def validate_crop(self, crop_id: int) -> Crop:
        crop = self.db.scalar(
            select(Crop).where(Crop.id == crop_id)
        )

        if crop is None:
            raise ValueError(
                f"Crop with ID {crop_id} was not found."
            )

        if not crop.is_active:
            raise ValueError(
                f"Crop '{crop.name}' is inactive."
            )

        return crop

    def validate_price(self, price) -> Decimal:
        try:
            decimal_price = Decimal(str(price))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                "Price must be a valid numeric value."
            )

        if decimal_price <= 0:
            raise ValueError(
                "Price must be greater than zero."
            )

        return decimal_price

    def validate_optional_price(
        self,
        price,
        field_name: str,
    ):
        if price is None:
            return None

        try:
            decimal_price = Decimal(str(price))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(
                f"{field_name} must be a valid numeric value."
            )

        if decimal_price < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

        return decimal_price

    def validate_unit(self, unit: str) -> str:
        if not unit:
            raise ValueError("Unit is required.")

        normalized = unit.strip().upper()

        if len(normalized) > self.MAX_UNIT_LENGTH:
            raise ValueError(
                f"Unit cannot exceed {self.MAX_UNIT_LENGTH} characters."
            )

        if normalized not in self.SUPPORTED_UNITS:
            raise ValueError(
                f"Unsupported unit '{normalized}'. "
                f"Supported units: "
                f"{', '.join(sorted(self.SUPPORTED_UNITS))}."
            )

        return normalized

    def validate_currency(self, currency: str) -> str:
        if not currency:
            raise ValueError("Currency is required.")

        normalized = currency.strip().upper()

        if len(normalized) > self.MAX_CURRENCY_LENGTH:
            raise ValueError(
                f"Currency cannot exceed "
                f"{self.MAX_CURRENCY_LENGTH} characters."
            )

        return normalized

    def validate_source(self, source: str) -> str:
        if not source:
            raise ValueError("Source is required.")

        normalized = source.strip()

        if not normalized:
            raise ValueError("Source cannot be empty.")

        if len(normalized) > self.MAX_SOURCE_LENGTH:
            raise ValueError(
                f"Source cannot exceed "
                f"{self.MAX_SOURCE_LENGTH} characters."
            )

        return normalized

    def validate_source_reference(
        self,
        source_reference: Optional[str],
    ) -> Optional[str]:
        if source_reference is None:
            return None

        normalized = str(source_reference).strip()

        if not normalized:
            return None

        if len(normalized) > self.MAX_SOURCE_REFERENCE_LENGTH:
            raise ValueError(
                "Source reference cannot exceed "
                f"{self.MAX_SOURCE_REFERENCE_LENGTH} characters."
            )

        return normalized

    def validate_date(self, price_date) -> datetime:
        if price_date is None:
            raise ValueError("Price date is required.")

        if isinstance(price_date, datetime):
            return price_date

        if hasattr(price_date, "year") and hasattr(
            price_date,
            "month",
        ) and hasattr(price_date, "day"):
            return datetime(
                price_date.year,
                price_date.month,
                price_date.day,
            )

        if isinstance(price_date, str):
            value = price_date.strip()

            if not value:
                raise ValueError(
                    "Price date cannot be empty."
                )

            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass

            try:
                return datetime.strptime(
                    value,
                    "%Y-%m-%d",
                )
            except ValueError:
                raise ValueError(
                    "Invalid price date. Use YYYY-MM-DD "
                    "or an ISO datetime."
                )

        raise ValueError(
            "Price date must be a datetime, date, "
            "or ISO date/datetime string."
        )

    # ============================================================
    # DUPLICATE CHECK
    # ============================================================

    def find_existing_price(
        self,
        market_id: int,
        crop_id: int,
        price_date: datetime,
        unit: str,
        quality_grade: Optional[str] = None,
    ) -> Optional[MarketPrice]:

        query = select(MarketPrice).where(
            MarketPrice.market_id == market_id,
            MarketPrice.crop_id == crop_id,
            MarketPrice.price_date == price_date,
            MarketPrice.unit == unit,
        )

        if quality_grade is None:
            query = query.where(
                MarketPrice.quality_grade.is_(None)
            )
        else:
            query = query.where(
                MarketPrice.quality_grade == quality_grade
            )

        return self.db.scalar(query)

    # ============================================================
    # INGEST ONE PRICE
    # ============================================================

    def ingest_price(
        self,
        market_id: int,
        crop_id: int,
        price,
        price_date,
        currency: str,
        unit: str,
        source: str,
        source_reference: Optional[str] = None,
        min_price=None,
        max_price=None,
        quality_grade: Optional[str] = None,
        notes: Optional[str] = None,
        skip_duplicates: bool = True,
    ) -> dict:

        market = self.validate_market(market_id)
        crop = self.validate_crop(crop_id)

        validated_price = self.validate_price(price)

        validated_min_price = self.validate_optional_price(
            min_price,
            "Minimum price",
        )

        validated_max_price = self.validate_optional_price(
            max_price,
            "Maximum price",
        )

        if (
            validated_min_price is not None
            and validated_max_price is not None
            and validated_min_price > validated_max_price
        ):
            raise ValueError(
                "Minimum price cannot be greater than maximum price."
            )

        if (
            validated_min_price is not None
            and validated_price < validated_min_price
        ):
            raise ValueError(
                "Price cannot be lower than minimum price."
            )

        if (
            validated_max_price is not None
            and validated_price > validated_max_price
        ):
            raise ValueError(
                "Price cannot be higher than maximum price."
            )

        validated_date = self.validate_date(price_date)
        validated_currency = self.validate_currency(currency)
        validated_unit = self.validate_unit(unit)
        validated_source = self.validate_source(source)
        validated_reference = self.validate_source_reference(
            source_reference
        )

        if quality_grade is not None:
            quality_grade = quality_grade.strip() or None

        if notes is not None:
            notes = notes.strip() or None

        existing = self.find_existing_price(
            market_id=market_id,
            crop_id=crop_id,
            price_date=validated_date,
            unit=validated_unit,
            quality_grade=quality_grade,
        )

        if existing is not None:

            if skip_duplicates:
                return {
                    "status": "DUPLICATE",
                    "message": (
                        "Market price already exists for this "
                        "market, crop, date, unit, and quality grade."
                    ),
                    "price_id": existing.id,
                    "market_id": existing.market_id,
                    "crop_id": existing.crop_id,
                    "price_date": existing.price_date,
                    "price": existing.price,
                    "currency": existing.currency,
                    "unit": existing.unit,
                    "source": existing.source,
                }

            raise ValueError(
                "Market price already exists for this "
                "market, crop, date, unit, and quality grade."
            )

        market_price = MarketPrice(
            market_id=market.id,
            crop_id=crop.id,
            price_date=validated_date,
            price=validated_price,
            currency=validated_currency,
            unit=validated_unit,
            min_price=validated_min_price,
            max_price=validated_max_price,
            source=validated_source,
            source_reference=validated_reference,
            quality_grade=quality_grade,
            notes=notes,
        )

        self.db.add(market_price)
        self.db.commit()
        self.db.refresh(market_price)

        return {
            "status": "INSERTED",
            "message": "Market price successfully ingested.",
            "price_id": market_price.id,
            "market_id": market_price.market_id,
            "market_name": market.name,
            "crop_id": market_price.crop_id,
            "crop_name": crop.name,
            "price_date": market_price.price_date,
            "price": market_price.price,
            "currency": market_price.currency,
            "unit": market_price.unit,
            "source": market_price.source,
            "source_reference": market_price.source_reference,
            "quality_grade": market_price.quality_grade,
        }

    # ============================================================
    # INGEST MANY PRICES
    # ============================================================

    def ingest_prices(
        self,
        records: list[dict],
        skip_duplicates: bool = True,
    ) -> dict:

        results = []

        inserted = 0
        duplicates = 0
        failed = 0

        for index, record in enumerate(records, start=1):

            try:
                result = self.ingest_price(
                    skip_duplicates=skip_duplicates,
                    **record,
                )

                results.append(
                    {
                        "record_number": index,
                        **result,
                    }
                )

                if result["status"] == "INSERTED":
                    inserted += 1

                elif result["status"] == "DUPLICATE":
                    duplicates += 1

            except Exception as exc:

                failed += 1

                results.append(
                    {
                        "record_number": index,
                        "status": "FAILED",
                        "message": str(exc),
                    }
                )

        if failed == 0:
            status = "SUCCESS"
        elif inserted > 0 or duplicates > 0:
            status = "PARTIAL_SUCCESS"
        else:
            status = "FAILED"

        return {
            "status": status,
            "total_records": len(records),
            "inserted": inserted,
            "duplicates": duplicates,
            "failed": failed,
            "results": results,
        }
