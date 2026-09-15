"""
FarmIQ - FAOSTAT Rwanda Potato Producer Price INGESTION

============================================================
PURPOSE
============================================================

Retrieve real FAOSTAT Rwanda Potato producer-price records
and safely insert them into the FarmIQ MarketPrice table.

============================================================
SOURCE
============================================================

FAOSTAT Agricultural Producer Prices

Country:
    Rwanda

M49:
    646

Item:
    Potatoes

Item code:
    116

Frequency:
    Monthly

Source unit:
    RWF / tonne

FarmIQ unit:
    RWF / KG

Conversion:
    RWF/kg = RWF/tonne / 1000

============================================================
TARGET
============================================================

Market ID:
    2

Market:
    Rwanda National Producer Price

Market level:
    NATIONAL

Market type:
    FARM_GATE

Crop ID:
    1

Crop:
    Irish Potato

============================================================
SAFETY
============================================================

This script:

    - validates the destination market
    - validates the destination crop
    - retrieves real FAOSTAT data
    - validates every record
    - converts RWF/tonne to RWF/kg
    - checks duplicates
    - inserts only new records
    - uses ONE database transaction
    - rolls back everything if an error occurs
    - verifies the number of inserted records
    - commits only after successful verification

It does NOT:

    - modify existing records
    - modify Gisenyi Market
    - delete records
    - insert duplicate records

============================================================
"""

from __future__ import annotations

import csv
import io
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select


# ============================================================
# MAKE BACKEND ROOT IMPORTABLE
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# FARM-IQ IMPORTS
# ============================================================

from app.core.database import SessionLocal

from app.core.market_constants import (
    MARKET_LEVEL_NATIONAL,
    MARKET_TYPE_FARM_GATE,
)

from app.models.market import Market, MarketPrice

from app.models.models import Crop


# ============================================================
# FAOSTAT CONFIGURATION
# ============================================================

FAO_URL = (
    "https://api.data.apps.fao.org/api/v2/bigquery"
)

FAO_SQL_URL = (
    "https://data.apps.fao.org/"
    "catalog/dataset/"
    "ab62e545-a3ce-44d7-ab0d-9728cb638cc2/"
    "resource/"
    "d30487a2-82f2-4f97-a711-935d64eab444/"
    "download/"
    "prices-pp-producer-prices-query.sql"
)

FAO_COUNTRY_NAME = "Rwanda"

FAO_COUNTRY_CODE = 646

FAO_ITEM_NAME = "Potatoes"

FAO_ITEM_CODE = 116

FAO_FREQUENCY = "monthly"


# ============================================================
# FARM-IQ TARGET
# ============================================================

TARGET_MARKET_ID = 2

TARGET_CROP_ID = 1

TARGET_CURRENCY = "RWF"

TARGET_UNIT = "KG"

TARGET_SOURCE = "FAOSTAT"


# ============================================================
# HELPERS
# ============================================================

def decimal_value(
    value: Any,
) -> Decimal:

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


def convert_tonne_to_kg(
    price_per_tonne: Decimal,
) -> Decimal:

    return (
        price_per_tonne
        / Decimal("1000")
    )


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


def parse_date(
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

    year = parse_year(
        record.get("year")
        or record.get("Year")
    )

    month = parse_month(
        record.get("months")
        or record.get("month")
        or record.get("Month")
    )

    return date(
        year,
        month,
        1,
    )


# ============================================================
# FETCH FAOSTAT
# ============================================================

def fetch_fao_records() -> list[dict[str, Any]]:

    print("=" * 80)
    print("FETCHING REAL FAOSTAT DATA")
    print("=" * 80)
    print()

    print("Endpoint:")
    print(FAO_URL)
    print()

    print("Country:", FAO_COUNTRY_NAME)
    print("M49:", FAO_COUNTRY_CODE)
    print("Item:", FAO_ITEM_NAME)
    print("Item code:", FAO_ITEM_CODE)
    print("Frequency:", FAO_FREQUENCY)
    print()

    params = {
        "download": "true",
        "frequency": FAO_FREQUENCY,
        "item_code": FAO_ITEM_CODE,
        "sql_url": FAO_SQL_URL,
    }

    response = httpx.get(
        FAO_URL,
        params=params,
        timeout=60.0,
    )

    response.raise_for_status()

    print(
        "HTTP status:",
        response.status_code,
    )

    print()

    reader = csv.DictReader(
        io.StringIO(
            response.text
        )
    )

    records = []

    for row in reader:

        country_code = (
            row.get("m49_code")
            or row.get("M49 Code")
            or row.get("M49")
        )

        if str(
            country_code
        ).strip() != str(
            FAO_COUNTRY_CODE
        ):

            continue

        records.append(row)

    print(
        "Rwanda records retrieved:",
        len(records),
    )

    print()

    return records


# ============================================================
# VALIDATE RECORD
# ============================================================

def normalize_record(
    record: dict[str, Any],
) -> dict[str, Any]:

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

    source_price = (
        record.get(
            "producer_price_lcu_tonne_lcu"
        )
        or record.get(
            "Producer Price LCU/Tonne LCU"
        )
    )

    # --------------------------------------------------------
    # COUNTRY
    # --------------------------------------------------------

    if str(country).strip() != FAO_COUNTRY_NAME:

        raise ValueError(
            f"Unexpected country: {country}"
        )

    # --------------------------------------------------------
    # COUNTRY CODE
    # --------------------------------------------------------

    if str(country_code).strip() != str(
        FAO_COUNTRY_CODE
    ):

        raise ValueError(
            f"Unexpected M49 code: {country_code}"
        )

    # --------------------------------------------------------
    # ITEM
    # --------------------------------------------------------

    if str(item).strip() != FAO_ITEM_NAME:

        raise ValueError(
            f"Unexpected item: {item}"
        )

    # --------------------------------------------------------
    # ITEM CODE
    # --------------------------------------------------------

    if str(item_code).strip() != str(
        FAO_ITEM_CODE
    ):

        raise ValueError(
            f"Unexpected item code: {item_code}"
        )

    # --------------------------------------------------------
    # FREQUENCY
    # --------------------------------------------------------

    if str(frequency).strip().lower() != (
        FAO_FREQUENCY
    ):

        raise ValueError(
            f"Unexpected frequency: {frequency}"
        )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    price_date = parse_date(
        record
    )

    # --------------------------------------------------------
    # SOURCE PRICE
    # --------------------------------------------------------

    price_per_tonne = decimal_value(
        source_price
    )

    # --------------------------------------------------------
    # CONVERSION
    # --------------------------------------------------------

    price_per_kg = convert_tonne_to_kg(
        price_per_tonne
    )

    return {
        "market_id": TARGET_MARKET_ID,
        "crop_id": TARGET_CROP_ID,
        "price_date": price_date,
        "price": price_per_kg,
        "currency": TARGET_CURRENCY,
        "unit": TARGET_UNIT,
        "source": TARGET_SOURCE,
        "source_reference": "FAOSTAT",
        "quality_grade": None,
        "min_price": None,
        "max_price": None,
        "notes": (
            "FAOSTAT Agricultural Producer Price | "
            "Rwanda | Potatoes | "
            "National farm-gate producer price | "
            f"Source price: "
            f"{price_per_tonne} RWF/tonne"
        ),
    }


# ============================================================
# VALIDATE TARGET MARKET
# ============================================================

def validate_target_market(
    db,
) -> Market:

    market = db.scalar(
        select(Market).where(
            Market.id == TARGET_MARKET_ID
        )
    )

    if market is None:

        raise RuntimeError(
            f"Target market ID {TARGET_MARKET_ID} "
            "does not exist."
        )

    if market.name != (
        "Rwanda National Producer Price"
    ):

        raise RuntimeError(
            "Target market name does not match "
            "the expected FAOSTAT market."
        )

    if market.country != FAO_COUNTRY_NAME:

        raise RuntimeError(
            "Target market country is not Rwanda."
        )

    if market.market_level != (
        MARKET_LEVEL_NATIONAL
    ):

        raise RuntimeError(
            "Target market is not NATIONAL."
        )

    if market.market_type != (
        MARKET_TYPE_FARM_GATE
    ):

        raise RuntimeError(
            "Target market is not FARM_GATE."
        )

    if market.source != TARGET_SOURCE:

        raise RuntimeError(
            "Target market source is not FAOSTAT."
        )

    if not market.is_active:

        raise RuntimeError(
            "Target market is inactive."
        )

    return market


# ============================================================
# VALIDATE TARGET CROP
# ============================================================

def validate_target_crop(
    db,
) -> Crop:

    crop = db.scalar(
        select(Crop).where(
            Crop.id == TARGET_CROP_ID
        )
    )

    if crop is None:

        raise RuntimeError(
            f"Target crop ID {TARGET_CROP_ID} "
            "does not exist."
        )

    if crop.name != "Irish Potato":

        raise RuntimeError(
            "Target crop is not Irish Potato."
        )

    if not crop.is_active:

        raise RuntimeError(
            "Target crop is inactive."
        )

    return crop


# ============================================================
# CHECK DUPLICATE
# ============================================================

def find_duplicate(
    db,
    normalized: dict[str, Any],
):

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

    return db.scalar(
        statement
    )


# ============================================================
# MAIN INGESTION
# ============================================================

def main() -> None:

    print()
    print("=" * 80)
    print("FARMIQ - FAOSTAT RWANDA POTATO PRICE INGESTION")
    print("=" * 80)
    print()

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # VALIDATE TARGETS
        # ----------------------------------------------------

        print("Validating target market...")

        market = validate_target_market(
            db
        )

        print(
            "✓ Market:",
            market.id,
            market.name,
        )

        print()

        print("Validating target crop...")

        crop = validate_target_crop(
            db
        )

        print(
            "✓ Crop:",
            crop.id,
            crop.name,
        )

        print()

        # ----------------------------------------------------
        # FETCH SOURCE
        # ----------------------------------------------------

        records = fetch_fao_records()

        if not records:

            raise RuntimeError(
                "No FAOSTAT Rwanda records found."
            )

        # ----------------------------------------------------
        # NORMALIZE AND VALIDATE
        # ----------------------------------------------------

        normalized_records = []

        validation_errors = []

        for index, record in enumerate(
            records,
            start=1,
        ):

            try:

                normalized = normalize_record(
                    record
                )

                normalized_records.append(
                    normalized
                )

            except Exception as exc:

                validation_errors.append(
                    {
                        "record": index,
                        "error": str(exc),
                    }
                )

        print("=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print()

        print(
            "Source records:",
            len(records),
        )

        print(
            "Valid records:",
            len(normalized_records),
        )

        print(
            "Validation errors:",
            len(validation_errors),
        )

        print()

        if validation_errors:

            for error in validation_errors:

                print(
                    f"Record #{error['record']}: "
                    f"{error['error']}"
                )

            raise RuntimeError(
                "Validation failed. "
                "Nothing will be inserted."
            )

        # ----------------------------------------------------
        # CHECK DUPLICATES
        # ----------------------------------------------------

        new_records = []

        duplicate_records = []

        for normalized in normalized_records:

            duplicate = find_duplicate(
                db,
                normalized,
            )

            if duplicate:

                duplicate_records.append(
                    (
                        normalized,
                        duplicate,
                    )
                )

            else:

                new_records.append(
                    normalized
                )

        print("=" * 80)
        print("DUPLICATE CHECK")
        print("=" * 80)
        print()

        print(
            "Validated:",
            len(normalized_records),
        )

        print(
            "Already existing:",
            len(duplicate_records),
        )

        print(
            "New records:",
            len(new_records),
        )

        print()

        # ----------------------------------------------------
        # DISPLAY INSERT PLAN
        # ----------------------------------------------------

        print("=" * 80)
        print("INSERT PLAN")
        print("=" * 80)
        print()

        if not new_records:

            print(
                "No new records need to be inserted."
            )

            print()

            print(
                "FAOSTAT ingestion is already up to date."
            )

            return

        print(
            f"{len(new_records)} records "
            "will be inserted."
        )

        print()

        print(
            "First record:"
        )

        first = new_records[0]

        print(
            first["price_date"],
            first["price"],
            first["currency"],
            "/",
            first["unit"],
        )

        print()

        print(
            "Last record:"
        )

        last = new_records[-1]

        print(
            last["price_date"],
            last["price"],
            last["currency"],
            "/",
            last["unit"],
        )

        print()

        # ----------------------------------------------------
        # INSERT TRANSACTION
        # ----------------------------------------------------

        print("=" * 80)
        print("BEGINNING DATABASE TRANSACTION")
        print("=" * 80)
        print()

        inserted_count = 0

        inserted_ids = []

        for normalized in new_records:

            price = MarketPrice(
                market_id=normalized[
                    "market_id"
                ],

                crop_id=normalized[
                    "crop_id"
                ],

                price_date=normalized[
                    "price_date"
                ],

                price=normalized[
                    "price"
                ],

                currency=normalized[
                    "currency"
                ],

                unit=normalized[
                    "unit"
                ],

                source=normalized[
                    "source"
                ],

                source_reference=normalized[
                    "source_reference"
                ],

                quality_grade=normalized[
                    "quality_grade"
                ],

                min_price=normalized[
                    "min_price"
                ],

                max_price=normalized[
                    "max_price"
                ],

                notes=normalized[
                    "notes"
                ],
            )

            db.add(price)

            inserted_count += 1

        # ----------------------------------------------------
        # FLUSH
        # ----------------------------------------------------

        db.flush()

        print(
            "Records staged:",
            inserted_count,
        )

        print()

        # ----------------------------------------------------
        # VERIFY STAGED RECORD COUNT
        # ----------------------------------------------------

        if inserted_count != len(
            new_records
        ):

            raise RuntimeError(
                "Inserted count does not match "
                "expected new-record count."
            )

        # ----------------------------------------------------
        # REFRESH IDs
        # ----------------------------------------------------

        for normalized in new_records:

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

            result = db.scalar(
                statement
            )

            if result:

                inserted_ids.append(
                    result.id
                )

        # ----------------------------------------------------
        # VERIFY DATABASE ROW COUNT
        # ----------------------------------------------------

        if len(inserted_ids) != len(
            new_records
        ):

            raise RuntimeError(
                "Database verification failed. "
                "Expected all staged records "
                "to be present."
            )

        print(
            "Database verification:",
            len(inserted_ids),
            "/",
            len(new_records),
        )

        print()

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        print(
            "All verification checks passed."
        )

        print(
            "Committing transaction..."
        )

        db.commit()

        print()

        print(
            "✓ TRANSACTION COMMITTED"
        )

        print()

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        print("=" * 80)
        print("FAOSTAT INGESTION COMPLETE")
        print("=" * 80)
        print()

        print(
            "FAOSTAT records retrieved:",
            len(records),
        )

        print(
            "Records validated:",
            len(normalized_records),
        )

        print(
            "Duplicates skipped:",
            len(duplicate_records),
        )

        print(
            "New records inserted:",
            len(new_records),
        )

        print(
            "Transaction status:",
            "COMMITTED",
        )

        print()

        print(
            "Market:",
            market.id,
            market.name,
        )

        print(
            "Crop:",
            crop.id,
            crop.name,
        )

        print()

    except Exception as exc:

        print()
        print("=" * 80)
        print("INGESTION FAILED")
        print("=" * 80)
        print()

        print(
            type(exc).__name__,
            ":",
            exc,
        )

        print()

        print(
            "ROLLING BACK TRANSACTION..."
        )

        db.rollback()

        print(
            "✓ ROLLBACK COMPLETE"
        )

        print()
        print(
            "NO PARTIAL TRANSACTION WAS COMMITTED."
        )

        raise

    finally:

        db.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
