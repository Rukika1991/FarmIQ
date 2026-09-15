"""
FarmIQ - FAOSTAT Rwanda Potato Producer Price DRY RUN

============================================================
PURPOSE
============================================================

Retrieve real FAOSTAT Rwanda Potato producer-price records,
validate them, normalize them for FarmIQ, convert the source
unit from RWF/tonne to RWF/kg, and compare them against the
existing FarmIQ database.

============================================================
CRITICAL SAFETY RULE
============================================================

THIS SCRIPT IS DRY-RUN ONLY.

It MUST NOT:

    - INSERT records
    - UPDATE records
    - DELETE records
    - COMMIT transactions
    - Call MarketIngestionService.ingest_price()
    - Call MarketIngestionService.ingest_prices()

The database is opened ONLY for READ operations so we can
check whether records already exist.

============================================================
SOURCE
============================================================

FAOSTAT
Country: Rwanda
M49: 646
Item: Potatoes
Item code: 116
Frequency: Monthly

Source unit:
    RWF / tonne

FarmIQ target unit:
    RWF / KG

Conversion:
    RWF/kg = RWF/tonne / 1000

============================================================
"""

from __future__ import annotations

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

from app.models.market import MarketPrice


# ============================================================
# SAFETY
# ============================================================

DRY_RUN = True


# ============================================================
# FAOSTAT CONFIGURATION
# ============================================================

FAO_URL = (
    "https://api.data.apps.fao.org/api/v2/bigquery"
)

FAO_ITEM_CODE = 116

FAO_COUNTRY_CODE = 646

FAO_COUNTRY_NAME = "Rwanda"

FAO_ITEM_NAME = "Potatoes"

FAO_FREQUENCY = "monthly"


# ============================================================
# FARM-IQ CONFIGURATION
# ============================================================

FARMIQ_MARKET_ID = 2

FARMIQ_CROP_ID = 1

TARGET_CURRENCY = "RWF"

TARGET_UNIT = "KG"


# ============================================================
# FAOSTAT SQL RESOURCE
# ============================================================

FAO_SQL_URL = (
    "https://data.apps.fao.org/"
    "catalog/dataset/"
    "ab62e545-a3ce-44d7-ab0d-9728cb638cc2/"
    "resource/"
    "d30487a2-82f2-4f97-a711-935d64eab444/"
    "download/"
    "prices-pp-producer-prices-query.sql"
)


# ============================================================
# HELPERS
# ============================================================

def decimal_value(
    value: Any,
) -> Decimal:

    if value is None:
        raise ValueError(
            "Price value is missing."
        )

    if isinstance(value, Decimal):
        result = value

    else:
        try:
            result = Decimal(
                str(value).strip()
            )

        except (
            InvalidOperation,
            ValueError,
        ) as exc:

            raise ValueError(
                f"Invalid price value: {value}"
            ) from exc

    if result <= 0:
        raise ValueError(
            f"Price must be greater than zero: {result}"
        )

    return result


def convert_tonne_to_kg(
    price_per_tonne: Decimal,
) -> Decimal:

    return (
        price_per_tonne / Decimal("1000")
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


def parse_date(
    value: Any,
    year: int,
    month_number: int,
) -> date:

    if value:

        value_text = str(value).strip()

        try:

            return date.fromisoformat(
                value_text[:10]
            )

        except ValueError:

            pass

    return date(
        year,
        month_number,
        1,
    )


def month_number(
    month: str,
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

    normalized = str(
        month
    ).strip()

    if normalized.isdigit():

        number = int(normalized)

        if 1 <= number <= 12:
            return number

    if normalized in months:
        return months[normalized]

    raise ValueError(
        f"Invalid month: {month}"
    )


# ============================================================
# FETCH FAOSTAT
# ============================================================

def fetch_fao_records() -> list[dict[str, Any]]:

    print("=" * 80)
    print("FETCHING REAL FAOSTAT DATA")
    print("=" * 80)
    print()

    print("FAOSTAT endpoint:")
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

    payload = response.text

    print(
        "FAOSTAT HTTP status:",
        response.status_code,
    )

    print()

    # --------------------------------------------------------
    # The inspection endpoint returns CSV text.
    # Reuse the CSV parsing logic from the inspection process.
    # --------------------------------------------------------

    import csv
    import io

    reader = csv.DictReader(
        io.StringIO(payload)
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

    return records


# ============================================================
# VALIDATE FAOSTAT RECORD
# ============================================================

def validate_record(
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

    year_value = (
        record.get("year")
        or record.get("Year")
    )

    month_value = (
        record.get("months")
        or record.get("month")
        or record.get("Month")
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
    # YEAR
    # --------------------------------------------------------

    year = parse_year(
        year_value
    )

    # --------------------------------------------------------
    # MONTH
    # --------------------------------------------------------

    month = str(
        month_value
    ).strip()

    month_no = month_number(
        month
    )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    source_date = (
        record.get("date")
        or record.get("Date")
    )

    price_date = parse_date(
        source_date,
        year,
        month_no,
    )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    price_per_tonne = decimal_value(
        source_price
    )

    # --------------------------------------------------------
    # CONVERT
    # --------------------------------------------------------

    price_per_kg = convert_tonne_to_kg(
        price_per_tonne
    )

    return {
        "country": country,
        "country_code": int(country_code),
        "item": item,
        "item_code": int(item_code),
        "frequency": frequency,
        "year": year,
        "month": month,
        "price_date": price_date,
        "source_price_per_tonne": price_per_tonne,
        "farm_iq_price_per_kg": price_per_kg,
        "currency": TARGET_CURRENCY,
        "unit": TARGET_UNIT,
        "market_id": FARMIQ_MARKET_ID,
        "crop_id": FARMIQ_CROP_ID,
        "source": "FAOSTAT",
    }


# ============================================================
# CHECK EXISTING FARM-IQ PRICE
# ============================================================

def existing_price(
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
# PRINT RECORD
# ============================================================

def print_record(
    number: int,
    normalized: dict[str, Any],
    duplicate: bool,
):

    print("-" * 80)

    print(
        f"Record #{number}"
    )

    print("-" * 80)

    print(
        "Date:",
        normalized["price_date"],
    )

    print(
        "FAOSTAT price:",
        normalized[
            "source_price_per_tonne"
        ],
        "RWF/tonne",
    )

    print(
        "FarmIQ price:",
        normalized[
            "farm_iq_price_per_kg"
        ],
        "RWF/kg",
    )

    print(
        "Market ID:",
        normalized["market_id"],
    )

    print(
        "Crop ID:",
        normalized["crop_id"],
    )

    print(
        "Source:",
        normalized["source"],
    )

    print(
        "Status:",
        "DUPLICATE / ALREADY EXISTS"
        if duplicate
        else "NEW / WOULD BE INSERTED",
    )

    print()


# ============================================================
# MAIN DRY RUN
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # SAFETY GUARD
    # --------------------------------------------------------

    if DRY_RUN is not True:

        raise RuntimeError(
            "SAFETY ERROR: "
            "This script is only allowed to run "
            "with DRY_RUN=True."
        )

    print()
    print("=" * 80)
    print("FARMIQ - FAOSTAT POTATO PRODUCER PRICE DRY RUN")
    print("=" * 80)
    print()

    print("DRY_RUN:", DRY_RUN)
    print()

    print(
        "DATABASE WRITE OPERATIONS ARE DISABLED."
    )

    print()

    # --------------------------------------------------------
    # FETCH
    # --------------------------------------------------------

    records = fetch_fao_records()

    print(
        "Rwanda records retrieved:",
        len(records),
    )

    print()

    if not records:

        print(
            "No Rwanda Potato records found."
        )

        return

    # --------------------------------------------------------
    # DATABASE READ-ONLY SESSION
    # --------------------------------------------------------

    db = SessionLocal()

    validated = []

    validation_errors = []

    duplicate_count = 0

    new_count = 0

    try:

        # ----------------------------------------------------
        # VALIDATE ALL RECORDS
        # ----------------------------------------------------

        for index, record in enumerate(
            records,
            start=1,
        ):

            try:

                normalized = validate_record(
                    record
                )

                existing = existing_price(
                    db,
                    normalized,
                )

                duplicate = (
                    existing is not None
                )

                if duplicate:

                    duplicate_count += 1

                else:

                    new_count += 1

                validated.append(
                    (
                        normalized,
                        duplicate,
                    )
                )

            except Exception as exc:

                validation_errors.append(
                    {
                        "record": index,
                        "error": str(exc),
                    }
                )

        # ----------------------------------------------------
        # PRINT SUMMARY
        # ----------------------------------------------------

        print("=" * 80)
        print("DRY-RUN VALIDATION SUMMARY")
        print("=" * 80)
        print()

        print(
            "Records retrieved:",
            len(records),
        )

        print(
            "Records validated:",
            len(validated),
        )

        print(
            "Validation errors:",
            len(validation_errors),
        )

        print(
            "Already in FarmIQ:",
            duplicate_count,
        )

        print(
            "New records:",
            new_count,
        )

        print()

        # ----------------------------------------------------
        # PRINT VALIDATION ERRORS
        # ----------------------------------------------------

        if validation_errors:

            print("=" * 80)
            print("VALIDATION ERRORS")
            print("=" * 80)
            print()

            for error in validation_errors:

                print(
                    f"Record #{error['record']}: "
                    f"{error['error']}"
                )

            print()

        # ----------------------------------------------------
        # PRINT ALL NORMALIZED RECORDS
        # ----------------------------------------------------

        print("=" * 80)
        print("NORMALIZED FARM-IQ RECORDS")
        print("=" * 80)
        print()

        for index, (
            normalized,
            duplicate,
        ) in enumerate(
            validated,
            start=1,
        ):

            print_record(
                index,
                normalized,
                duplicate,
            )

        # ----------------------------------------------------
        # FINAL SAFETY MESSAGE
        # ----------------------------------------------------

        print("=" * 80)
        print("DATABASE SAFETY CHECK")
        print("=" * 80)
        print()

        print(
            "DRY_RUN:",
            DRY_RUN,
        )

        print(
            "INSERT:",
            "DISABLED",
        )

        print(
            "UPDATE:",
            "DISABLED",
        )

        print(
            "DELETE:",
            "DISABLED",
        )

        print(
            "COMMIT:",
            "DISABLED",
        )

        print()

        print(
            "The database was used only for "
            "read-only duplicate checks."
        )

        print()

        print(
            "NO FAOSTAT PRICE RECORDS WERE INSERTED."
        )

        print()

        print(
            "DRY RUN COMPLETE."
        )

    finally:

        db.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
