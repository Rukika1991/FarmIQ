from decimal import Decimal

from app.services.fao_adapter import (
    FAOProducerPriceAdapter,
)


def main():
    print("=" * 70)
    print("FARMIQ FAOSTAT PRODUCER PRICE ADAPTER TEST")
    print("=" * 70)

    adapter = FAOProducerPriceAdapter()

    # ============================================================
    # TEST 1 — SINGLE RECORD NORMALIZATION
    # ============================================================

    print("\n1. Testing single FAO record normalization...")

    raw_record = {
        "Area": "Rwanda",
        "Item": "Potatoes",
        "Year": 2024,
        "Value": "0.4556",
        "Unit": "USD/kg",
        "Currency": "USD",
    }

    record = adapter.normalize_fao_record(
        record=raw_record,
        market_id=1,
        crop_id=1,
    )

    print("\nNormalized FAO record:")
    print(record)

    assert record.market_id == 1
    assert record.crop_id == 1

    # IMPORTANT:
    # Compare Decimal with Decimal, not Decimal with float.
    assert record.price == Decimal("0.4556")

    assert record.price_date.year == 2024
    assert record.price_date.month == 1
    assert record.price_date.day == 1

    assert record.currency == "USD"
    assert record.unit == "KG"
    assert record.source == "FAOSTAT_PRODUCER_PRICE"

    print("✓ Single record normalization passed")

    # ============================================================
    # TEST 2 — MULTIPLE RECORDS
    # ============================================================

    print("\n2. Testing multiple FAO records...")

    raw_records = [
        {
            "Area": "Rwanda",
            "Item": "Potatoes",
            "Year": 2022,
            "Value": "0.4000",
            "Unit": "USD/kg",
            "Currency": "USD",
        },
        {
            "Area": "Rwanda",
            "Item": "Potatoes",
            "Year": 2023,
            "Value": "0.4300",
            "Unit": "USD/kg",
            "Currency": "USD",
        },
        {
            "Area": "Rwanda",
            "Item": "Potatoes",
            "Year": 2024,
            "Value": "0.4556",
            "Unit": "USD/kg",
            "Currency": "USD",
        },
    ]

    records = adapter.normalize_fao_records(
        records=raw_records,
        market_id=1,
        crop_id=1,
    )

    print(
        f"Normalized records: {len(records)}"
    )

    for item in records:
        print(item)

    assert len(records) == 3

    assert records[0].price == Decimal("0.4000")
    assert records[1].price == Decimal("0.4300")
    assert records[2].price == Decimal("0.4556")

    assert records[0].price_date.year == 2022
    assert records[1].price_date.year == 2023
    assert records[2].price_date.year == 2024

    print("✓ Multiple record normalization passed")

    # ============================================================
    # TEST 3 — UNIT NORMALIZATION
    # ============================================================

    print("\n3. Testing FAO unit normalization...")

    assert (
        adapter._normalize_unit("USD/kg")
        == "KG"
    )

    assert (
        adapter._normalize_unit("kg")
        == "KG"
    )

    assert (
        adapter._normalize_unit("tonne")
        == "TONNE"
    )

    assert (
        adapter._normalize_unit("MT")
        == "TONNE"
    )

    print("✓ Unit normalization passed")

    # ============================================================
    # TEST 4 — YEAR DATE NORMALIZATION
    # ============================================================

    print("\n4. Testing year/date normalization...")

    year_date = adapter._extract_date(
        {
            "Year": 2024,
        }
    )

    assert year_date.year == 2024
    assert year_date.month == 1
    assert year_date.day == 1

    iso_date = adapter._extract_date(
        {
            "Date": "2024-06-15",
        }
    )

    assert iso_date.year == 2024
    assert iso_date.month == 6
    assert iso_date.day == 15

    print("✓ Date normalization passed")

    # ============================================================
    # TEST 5 — INVALID PRICE
    # ============================================================

    print("\n5. Testing invalid price validation...")

    try:
        adapter.normalize_fao_record(
            {
                "Area": "Rwanda",
                "Item": "Potatoes",
                "Year": 2024,
                "Value": "-10",
                "Unit": "USD/kg",
                "Currency": "USD",
            },
            market_id=1,
            crop_id=1,
        )

        raise AssertionError(
            "Negative price should have failed."
        )

    except ValueError as exc:
        print(
            f"✓ Invalid price rejected: {exc}"
        )

    # ============================================================
    # TEST 6 — MISSING PRICE
    # ============================================================

    print("\n6. Testing missing price validation...")

    try:
        adapter.normalize_fao_record(
            {
                "Area": "Rwanda",
                "Item": "Potatoes",
                "Year": 2024,
                "Unit": "USD/kg",
                "Currency": "USD",
            },
            market_id=1,
            crop_id=1,
        )

        raise AssertionError(
            "Missing price should have failed."
        )

    except ValueError as exc:
        print(
            f"✓ Missing price rejected: {exc}"
        )

    # ============================================================
    # IMPORTANT — NO DATABASE INSERTION
    # ============================================================

    print("\n7. Database safety check...")

    print(
        "✓ This test only normalizes FAO records."
    )

    print(
        "✓ No records were inserted into PostgreSQL."
    )

    # ============================================================
    # COMPLETE
    # ============================================================

    print("\n" + "=" * 70)
    print("ALL FAO ADAPTER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
