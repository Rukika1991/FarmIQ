from app.services.market_sources import (
    MarketPriceRecord,
    TestMarketSourceAdapter,
    FarmIQSourceAdapter,
    create_default_market_source_registry,
)


def main():
    print("=" * 70)
    print("FARMIQ MARKET SOURCE ADAPTER TEST")
    print("=" * 70)

    # ========================================================
    # TEST 1 — TEST SOURCE
    # ========================================================

    print("\n1. Testing TestMarketSourceAdapter...")

    adapter = TestMarketSourceAdapter()

    records = adapter.fetch(
        market_id=1,
        crop_id=1,
    )

    print(f"Records returned: {len(records)}")

    for record in records:
        print(record)

    assert len(records) == 2

    assert isinstance(
        records[0],
        MarketPriceRecord,
    )

    assert records[0].currency == "RWF"
    assert records[0].unit == "KG"

    # ========================================================
    # TEST 2 — FARM IQ SOURCE
    # ========================================================

    print("\n2. Testing FarmIQSourceAdapter...")

    farmiq_adapter = FarmIQSourceAdapter()

    records = farmiq_adapter.fetch(
        [
            {
                "market_id": 1,
                "crop_id": 1,
                "price": "500",
                "price_date": "2026-09-21",
                "currency": "rwf",
                "unit": "kg",
                "source_reference": "Manual test",
                "quality_grade": "STANDARD",
            }
        ]
    )

    print(f"Records returned: {len(records)}")
    print(records[0])

    assert len(records) == 1
    assert records[0].price == 500
    assert records[0].currency == "RWF"
    assert records[0].unit == "KG"
    assert records[0].source == "FARM_IQ"

    # ========================================================
    # TEST 3 — SOURCE REGISTRY
    # ========================================================

    print("\n3. Testing MarketSourceRegistry...")

    registry = create_default_market_source_registry()

    sources = registry.list_sources()

    print("Registered sources:")
    for source in sources:
        print(f"  - {source}")

    assert "FARM_IQ" in sources
    assert "TEST_SOURCE" in sources

    test_adapter = registry.get(
        "TEST_SOURCE"
    )

    assert isinstance(
        test_adapter,
        TestMarketSourceAdapter,
    )

    # ========================================================
    # TEST 4 — INVALID DATA
    # ========================================================

    print("\n4. Testing validation...")

    try:
        adapter.normalize(
            {
                "market_id": 1,
                "crop_id": 1,
                "price": -100,
                "price_date": "2026-09-21",
                "currency": "RWF",
                "unit": "KG",
            }
        )

        raise AssertionError(
            "Negative price should have failed."
        )

    except ValueError as exc:
        print(
            f"Correctly rejected invalid price: {exc}"
        )

    # ========================================================
    # COMPLETE
    # ========================================================

    print("\n" + "=" * 70)
    print("ALL MARKET SOURCE ADAPTER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
