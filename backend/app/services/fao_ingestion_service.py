"""
FarmIQ - Generic FAOSTAT Producer Price Ingestion Service

This service provides reusable ingestion logic for FAOSTAT
agricultural producer prices.

Responsibilities:
    1. Fetch FAOSTAT records
    2. Filter country/item
    3. Validate records
    4. Normalize dates and prices
    5. Convert source units
    6. Resolve FarmIQ market and crop
    7. Detect duplicates
    8. Insert records transactionally
    9. Verify insertion
    10. Commit only after successful verification

The service does NOT contain crop-specific business logic.

A caller supplies:
    - FAOSTAT country
    - FAOSTAT country code
    - FAOSTAT item
    - FAOSTAT item code
    - FarmIQ market ID
    - FarmIQ crop ID
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from sqlalchemy import select

from app.models.market import Market, MarketPrice
from app.models.models import Crop


# ============================================================
# DEFAULT FAOSTAT ENDPOINT
# ============================================================

DEFAULT_FAO_URL = (
    "https://api.data.apps.fao.org/api/v2/bigquery"
)


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass(frozen=True)
class FAOSTATIngestionConfig:
    """
    Configuration describing one FAOSTAT dataset ingestion.
    """

    country_name: str
    country_code: int

    item_name: str
    item_code: int

    frequency: str

    market_id: int
    crop_id: int

    currency: str = "RWF"
    unit: str = "KG"

    source: str = "FAOSTAT"

    source_unit: str = "RWF/tonne"

    target_unit: str = "RWF/kg"


# ============================================================
# INGESTION RESULT
# ============================================================

@dataclass
class FAOSTATIngestionResult:
    """
    Summary returned after an ingestion attempt.
    """

    source_records: int = 0
    validated_records: int = 0
    validation_errors: int = 0

    duplicate_records: int = 0
    new_records: int = 0

    inserted_records: int = 0

    transaction_committed: bool = False


# ============================================================
# SERVICE
# ============================================================

class FAOSTATIngestionService:
    """
    Generic FAOSTAT producer-price ingestion service.
    """

    def __init__(
        self,
        db,
        config: FAOSTATIngestionConfig,
        fao_url: str = DEFAULT_FAO_URL,
        sql_url: str | None = None,
    ):
        self.db = db
        self.config = config
        self.fao_url = fao_url
        self.sql_url = sql_url

    # ========================================================
    # FETCH
    # ========================================================

    def fetch_records(
        self,
    ) -> list[dict[str, Any]]:
        """
        Retrieve FAOSTAT records from the configured endpoint.
        """

        params = {
            "download": "true",
            "frequency": self.config.frequency,
            "item_code": self.config.item_code,
        }

        if self.sql_url:
            params["sql_url"] = self.sql_url

        response = httpx.get(
            self.fao_url,
            params=params,
            timeout=60.0,
        )

        response.raise_for_status()

        reader = csv.DictReader(
            io.StringIO(response.text)
        )

        records: list[dict[str, Any]] = []

        for row in reader:

            country_code = (
                row.get("m49_code")
                or row.get("M49 Code")
                or row.get("M49")
            )

            if str(
                country_code
            ).strip() != str(
                self.config.country_code
            ):

                continue

            records.append(row)

        return records

    # ========================================================
    # DECIMAL
    # ========================================================

    @staticmethod
    def decimal_value(
        value: Any,
    ) -> Decimal:
        """
        Convert a source price into Decimal safely.
        """

        if value is None:
            raise ValueError(
                "FAOSTAT price is missing."
            )

        try:

            result = Decimal(
                str(value).strip()
            )

        except (
            InvalidOperation,
            ValueError,
            TypeError,
        ) as exc:

            raise ValueError(
                f"Invalid FAOSTAT price: {value}"
            ) from exc

        if result <= 0:

            raise ValueError(
                f"FAOSTAT price must be greater than zero: {result}"
            )

        return result

    # ========================================================
    # UNIT CONVERSION
    # ========================================================

    @staticmethod
    def tonne_to_kg(
        price_per_tonne: Decimal,
    ) -> Decimal:
        """
        Convert RWF/tonne to RWF/kg.
        """

        return (
            price_per_tonne
            / Decimal("1000")
        )

    # ========================================================
    # YEAR
    # ========================================================

    @staticmethod
    def parse_year(
        value: Any,
    ) -> int:

        try:

            year = int(
                str(value).strip()
            )

        except (
            ValueError,
            TypeError,
        ) as exc:

            raise ValueError(
                f"Invalid year: {value}"
            ) from exc

        if year < 1900 or year > 2100:

            raise ValueError(
                f"Year outside expected range: {year}"
            )

        return year

    # ========================================================
    # MONTH
    # ========================================================

    @staticmethod
    def parse_month(
        value: Any,
    ) -> int:

        months = {
            "January": 1,
            "February": 2,
            "March": 3,
            "April": 4,
            "May": 5,
            "June": 6,
            "July": 7,
            "August": 8,
            "September": 9,
            "October": 10,
            "November": 11,
            "December": 12,
        }

        text = str(
            value
        ).strip()

        if text.isdigit():

            month = int(text)

            if 1 <= month <= 12:
                return month

        if text in months:
            return months[text]

        raise ValueError(
            f"Invalid month: {value}"
        )

    # ========================================================
    # DATE
    # ========================================================

    def parse_date(
        self,
        record: dict[str, Any],
    ) -> date:

        source_date = (
            record.get("date")
            or record.get("Date")
        )

        if source_date:

            text = str(
                source_date
            ).strip()

            try:

                return date.fromisoformat(
                    text[:10]
                )

            except ValueError:

                pass

        year = self.parse_year(
            record.get("year")
            or record.get("Year")
        )

        month = self.parse_month(
            record.get("months")
            or record.get("month")
            or record.get("Month")
        )

        return date(
            year,
            month,
            1,
        )

    # ========================================================
    # SOURCE PRICE EXTRACTION
    # ========================================================

    @staticmethod
    def extract_price(
        record: dict[str, Any],
    ) -> Any:

        possible_fields = [
            "producer_price_lcu_tonne_lcu",
            "Producer Price LCU/Tonne LCU",
            "Value",
            "Price",
        ]

        for field in possible_fields:

            value = record.get(field)

            if value not in (
                None,
                "",
            ):

                return value

        raise ValueError(
            "Could not find producer-price value "
            "in FAOSTAT record."
        )

    # ========================================================
    # NORMALIZE ONE RECORD
    # ========================================================

    def normalize_record(
        self,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate and normalize one FAOSTAT record.
        """

        country = (
            record.get("country_name_en")
            or record.get("Country")
            or record.get("country")
        )

        country_code = (
            record.get("m49_code")
            or record.get("M49 Code")
            or record.get("M49")
        )

        item = (
            record.get("item")
            or record.get("Item")
            or record.get("item_name")
        )

        item_code = (
            record.get("item_code")
            or record.get("Item Code")
        )

        frequency = (
            record.get("frequency")
            or record.get("Frequency")
        )

        # ----------------------------------------------------
        # COUNTRY
        # ----------------------------------------------------

        if str(country).strip() != (
            self.config.country_name
        ):

            raise ValueError(
                f"Unexpected country: {country}"
            )

        # ----------------------------------------------------
        # COUNTRY CODE
        # ----------------------------------------------------

        if str(country_code).strip() != str(
            self.config.country_code
        ):

            raise ValueError(
                f"Unexpected country code: "
                f"{country_code}"
            )

        # ----------------------------------------------------
        # ITEM
        # ----------------------------------------------------

        if str(item).strip() != (
            self.config.item_name
        ):

            raise ValueError(
                f"Unexpected item: {item}"
            )

        # ----------------------------------------------------
        # ITEM CODE
        # ----------------------------------------------------

        if str(item_code).strip() != str(
            self.config.item_code
        ):

            raise ValueError(
                f"Unexpected item code: "
                f"{item_code}"
            )

        # ----------------------------------------------------
        # FREQUENCY
        # ----------------------------------------------------

        if str(frequency).strip().lower() != (
            self.config.frequency.lower()
        ):

            raise ValueError(
                f"Unexpected frequency: "
                f"{frequency}"
            )

        # ----------------------------------------------------
        # DATE
        # ----------------------------------------------------

        price_date = self.parse_date(
            record
        )

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        source_price = self.extract_price(
            record
        )

        price_per_tonne = self.decimal_value(
            source_price
        )

        # ----------------------------------------------------
        # CONVERSION
        # ----------------------------------------------------

        if (
            self.config.source_unit.lower()
            == "rwf/tonne"
            and self.config.target_unit.lower()
            == "rwf/kg"
        ):

            price = self.tonne_to_kg(
                price_per_tonne
            )

        else:

            raise ValueError(
                "Unsupported unit conversion: "
                f"{self.config.source_unit} → "
                f"{self.config.target_unit}"
            )

        # ----------------------------------------------------
        # NORMALIZED RECORD
        # ----------------------------------------------------

        return {
            "market_id": self.config.market_id,
            "crop_id": self.config.crop_id,

            "price_date": price_date,

            "price": price,

            "currency": self.config.currency,
            "unit": self.config.unit,

            "source": self.config.source,

            "source_reference": "FAOSTAT",

            "quality_grade": None,

            "min_price": None,
            "max_price": None,

            "notes": (
                "FAOSTAT Agricultural Producer Price | "
                f"{self.config.country_name} | "
                f"{self.config.item_name} | "
                "National farm-gate producer price | "
                f"Source price: "
                f"{price_per_tonne} RWF/tonne"
            ),
        }

    # ========================================================
    # NORMALIZE ALL
    # ========================================================

    def normalize_records(
        self,
        records: list[dict[str, Any]],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        """
        Normalize all source records.

        Returns:
            valid_records
            errors
        """

        valid_records = []

        errors = []

        for index, record in enumerate(
            records,
            start=1,
        ):

            try:

                normalized = self.normalize_record(
                    record
                )

                valid_records.append(
                    normalized
                )

            except Exception as exc:

                errors.append(
                    {
                        "record": index,
                        "error": str(exc),
                    }
                )

        return (
            valid_records,
            errors,
        )

    # ========================================================
    # TARGET MARKET
    # ========================================================

    def validate_market(self) -> Market:
        """
        Verify the configured FarmIQ market.
        """

        market = self.db.scalar(
            select(Market).where(
                Market.id
                == self.config.market_id
            )
        )

        if market is None:

            raise RuntimeError(
                f"Market ID "
                f"{self.config.market_id} "
                "does not exist."
            )

        if not market.is_active:

            raise RuntimeError(
                "Configured market is inactive."
            )

        return market

    # ========================================================
    # TARGET CROP
    # ========================================================

    def validate_crop(self) -> Crop:
        """
        Verify the configured FarmIQ crop.
        """

        crop = self.db.scalar(
            select(Crop).where(
                Crop.id
                == self.config.crop_id
            )
        )

        if crop is None:

            raise RuntimeError(
                f"Crop ID "
                f"{self.config.crop_id} "
                "does not exist."
            )

        if not crop.is_active:

            raise RuntimeError(
                "Configured crop is inactive."
            )

        return crop

    # ========================================================
    # DUPLICATE
    # ========================================================

    def find_duplicate(
        self,
        normalized: dict[str, Any],
    ) -> MarketPrice | None:
        """
        Find an existing identical source observation.
        """

        statement = select(
            MarketPrice
        ).where(
            MarketPrice.market_id
            == normalized["market_id"],

            MarketPrice.crop_id
            == normalized["crop_id"],

            MarketPrice.price_date
            == normalized["price_date"],

            MarketPrice.currency
            == normalized["currency"],

            MarketPrice.unit
            == normalized["unit"],

            MarketPrice.source
            == normalized["source"],
        )

        return self.db.scalar(
            statement
        )

    # ========================================================
    # PREPARE NEW RECORDS
    # ========================================================

    def prepare_records(
        self,
        normalized_records: list[dict[str, Any]],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        """
        Separate records into:

            new records
            duplicates
        """

        new_records = []

        duplicates = []

        for normalized in normalized_records:

            duplicate = self.find_duplicate(
                normalized
            )

            if duplicate:

                duplicates.append(
                    normalized
                )

            else:

                new_records.append(
                    normalized
                )

        return (
            new_records,
            duplicates,
        )

    # ========================================================
    # INSERT
    # ========================================================

    def insert_records(
        self,
        records: list[dict[str, Any]],
    ) -> int:
        """
        Insert records inside the current transaction.

        This method does NOT commit.
        """

        for record in records:

            price = MarketPrice(
                market_id=record[
                    "market_id"
                ],

                crop_id=record[
                    "crop_id"
                ],

                price_date=record[
                    "price_date"
                ],

                price=record[
                    "price"
                ],

                currency=record[
                    "currency"
                ],

                unit=record[
                    "unit"
                ],

                source=record[
                    "source"
                ],

                source_reference=record[
                    "source_reference"
                ],

                quality_grade=record[
                    "quality_grade"
                ],

                min_price=record[
                    "min_price"
                ],

                max_price=record[
                    "max_price"
                ],

                notes=record[
                    "notes"
                ],
            )

            self.db.add(
                price
            )

        self.db.flush()

        return len(records)

    # ========================================================
    # VERIFY
    # ========================================================

    def verify_inserted_count(
        self,
        expected_count: int,
        before_count: int,
    ) -> int:
        """
        Verify that exactly expected_count records
        were added to the target market/crop/source.
        """

        statement = select(
            MarketPrice
        ).where(
            MarketPrice.market_id
            == self.config.market_id,

            MarketPrice.crop_id
            == self.config.crop_id,

            MarketPrice.source
            == self.config.source,
        )

        current_records = self.db.scalars(
            statement
        ).all()

        current_count = len(
            current_records
        )

        actual_added = (
            current_count
            - before_count
        )

        if actual_added != expected_count:

            raise RuntimeError(
                "Insertion verification failed. "
                f"Expected {expected_count}, "
                f"actual increase {actual_added}."
            )

        return actual_added

    # ========================================================
    # FULL INGESTION
    # ========================================================

    def ingest(
        self,
    ) -> FAOSTATIngestionResult:
        """
        Execute complete transactional ingestion.
        """

        result = FAOSTATIngestionResult()

        # ----------------------------------------------------
        # VALIDATE TARGETS
        # ----------------------------------------------------

        self.validate_market()
        self.validate_crop()

        # ----------------------------------------------------
        # BASELINE COUNT
        # ----------------------------------------------------

        before_statement = select(
            MarketPrice
        ).where(
            MarketPrice.market_id
            == self.config.market_id,

            MarketPrice.crop_id
            == self.config.crop_id,

            MarketPrice.source
            == self.config.source,
        )

        before_records = self.db.scalars(
            before_statement
        ).all()

        before_count = len(
            before_records
        )

        # ----------------------------------------------------
        # FETCH
        # ----------------------------------------------------

        records = self.fetch_records()

        result.source_records = len(
            records
        )

        if not records:

            raise RuntimeError(
                "FAOSTAT returned no records."
            )

        # ----------------------------------------------------
        # NORMALIZE
        # ----------------------------------------------------

        (
            normalized_records,
            errors,
        ) = self.normalize_records(
            records
        )

        result.validated_records = len(
            normalized_records
        )

        result.validation_errors = len(
            errors
        )

        if errors:

            error_text = "; ".join(
                (
                    f"record {error['record']}: "
                    f"{error['error']}"
                )
                for error in errors[:10]
            )

            raise RuntimeError(
                "FAOSTAT validation failed: "
                + error_text
            )

        # ----------------------------------------------------
        # DUPLICATES
        # ----------------------------------------------------

        (
            new_records,
            duplicates,
        ) = self.prepare_records(
            normalized_records
        )

        result.duplicate_records = len(
            duplicates
        )

        result.new_records = len(
            new_records
        )

        # ----------------------------------------------------
        # NOTHING NEW
        # ----------------------------------------------------

        if not new_records:

            result.inserted_records = 0

            result.transaction_committed = False

            return result

        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        inserted = self.insert_records(
            new_records
        )

        result.inserted_records = inserted

        # ----------------------------------------------------
        # VERIFY
        # ----------------------------------------------------

        verified = self.verify_inserted_count(
            expected_count=len(new_records),
            before_count=before_count,
        )

        if verified != inserted:

            raise RuntimeError(
                "Final insertion count mismatch."
            )

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        self.db.commit()

        result.transaction_committed = True

        return result
