"""
FarmIQ - FAOSTAT Rwanda Potato Producer Price Inspection

IMPORTANT:
    This script ONLY retrieves and displays FAOSTAT data.

    It does NOT:
        - insert into PostgreSQL
        - update MarketPrice
        - call MarketIngestionService
        - commit any transaction

Purpose:
    Inspect real FAOSTAT agricultural producer-price records for
    Rwanda and potatoes before deciding whether they are suitable
    for FarmIQ.
"""

from __future__ import annotations

import csv
import io
from decimal import Decimal
from typing import Any

import httpx


# ============================================================
# OFFICIAL FAO QUERY
# ============================================================

FAO_URL = (
    "https://api.data.apps.fao.org/api/v2/bigquery"
)

# Potatoes item code in the FAOSTAT producer-price dataset.
POTATO_ITEM_CODE = 116

# Rwanda M49 country code.
RWANDA_M49_CODE = 646


# ============================================================
# FETCH
# ============================================================

def fetch_fao_data() -> str:

    params = {
        "download": "true",
        "frequency": "monthly",
        "item_code": POTATO_ITEM_CODE,
        "sql_url": (
            "https://data.apps.fao.org/"
            "catalog/dataset/"
            "ab62e545-a3ce-44d7-ab0d-9728cb638cc2/"
            "resource/"
            "d30487a2-82f2-4f97-a711-935d64eab444/"
            "download/"
            "prices-pp-producer-prices-query.sql"
        ),
    }

    print("=" * 80)
    print("FAOSTAT REAL DATA INSPECTION")
    print("=" * 80)
    print()
    print("Source:")
    print(FAO_URL)
    print()
    print("Requested:")
    print("  Country : Rwanda")
    print("  Crop    : Potatoes")
    print("  Frequency: Monthly")
    print()

    response = httpx.get(
        FAO_URL,
        params=params,
        timeout=60.0,
    )

    response.raise_for_status()

    print("HTTP status:", response.status_code)
    print()

    return response.text


# ============================================================
# PARSE CSV
# ============================================================

def parse_records(csv_text: str) -> list[dict[str, Any]]:

    reader = csv.DictReader(
        io.StringIO(csv_text)
    )

    records = []

    for row in reader:

        country_code = row.get("m49_code")

        if str(country_code).strip() != str(RWANDA_M49_CODE):
            continue

        records.append(row)

    return records


# ============================================================
# INSPECTION
# ============================================================

def inspect_records(records: list[dict[str, Any]]):

    print("=" * 80)
    print("FILTERED RWANDA RECORDS")
    print("=" * 80)
    print()

    if not records:
        print("NO RWANDA RECORDS FOUND.")
        print()
        return

    print("Number of Rwanda records:", len(records))
    print()

    for index, record in enumerate(records, start=1):

        print("-" * 80)
        print(f"Record #{index}")
        print("-" * 80)

        print("Country:")
        print(" ", record.get("country_name_en"))

        print("M49 code:")
        print(" ", record.get("m49_code"))

        print("Item:")
        print(" ", record.get("item"))

        print("Item code:")
        print(" ", record.get("item_code"))

        print("Year:")
        print(" ", record.get("year"))

        print("Month:")
        print(" ", record.get("months"))

        print("Date:")
        print(" ", record.get("date"))

        print("Frequency:")
        print(" ", record.get("frequency"))

        print("Local currency / tonne:")
        print(
            " ",
            record.get(
                "producer_price_lcu_tonne_lcu"
            ),
        )

        print("Standard local currency / tonne:")
        print(
            " ",
            record.get(
                "producer_price_slc_tonne_slc"
            ),
        )

        print("USD / tonne:")
        print(
            " ",
            record.get(
                "producer_price_usd_tonne_usd"
            ),
        )

        print("LCU flag:")
        print(
            " ",
            record.get(
                "producer_price_lcu_tonne_lcu_flag"
            ),
        )

        print("USD flag:")
        print(
            " ",
            record.get(
                "producer_price_usd_tonne_usd_flag"
            ),
        )

        print()


# ============================================================
# DATA QUALITY CHECK
# ============================================================

def inspect_data_quality(records: list[dict[str, Any]]):

    print("=" * 80)
    print("BASIC DATA QUALITY CHECK")
    print("=" * 80)
    print()

    if not records:
        print("No records available.")
        return

    countries = {
        record.get("country_name_en")
        for record in records
    }

    items = {
        record.get("item")
        for record in records
    }

    frequencies = {
        record.get("frequency")
        for record in records
    }

    years = []

    prices = []

    for record in records:

        year = record.get("year")

        if year:
            try:
                years.append(int(year))
            except ValueError:
                pass

        price = record.get(
            "producer_price_lcu_tonne_lcu"
        )

        if price not in (None, ""):

            try:
                prices.append(
                    Decimal(str(price))
                )
            except Exception:
                pass

    print("Countries:")
    print(countries)
    print()

    print("Items:")
    print(items)
    print()

    print("Frequencies:")
    print(frequencies)
    print()

    if years:
        print("Year range:")
        print(min(years), "→", max(years))
        print()

    print("Records with LCU price:")
    print(len(prices))
    print()

    if prices:

        print("Minimum LCU price:")
        print(min(prices))

        print("Maximum LCU price:")
        print(max(prices))

        print()


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        csv_text = fetch_fao_data()

        records = parse_records(
            csv_text
        )

        inspect_records(records)

        inspect_data_quality(
            records
        )

        print("=" * 80)
        print("DATABASE SAFETY CHECK")
        print("=" * 80)
        print()
        print("NO DATABASE CONNECTION WAS USED.")
        print("NO INSERT WAS PERFORMED.")
        print("NO UPDATE WAS PERFORMED.")
        print("NO DELETE WAS PERFORMED.")
        print("NO COMMIT WAS PERFORMED.")
        print()
        print("Inspection complete.")

    except httpx.HTTPError as exc:

        print()
        print("=" * 80)
        print("FAOSTAT HTTP ERROR")
        print("=" * 80)
        print(exc)

    except Exception as exc:

        print()
        print("=" * 80)
        print("INSPECTION ERROR")
        print("=" * 80)
        print(type(exc).__name__)
        print(exc)


if __name__ == "__main__":
    main()
