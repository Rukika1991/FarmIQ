from datetime import date

from app.core.database import SessionLocal
from app.services.market_ingestion import MarketIngestionService


def main():
    db = SessionLocal()

    try:
        service = MarketIngestionService(db)

        print("=" * 70)
        print("FARMIQ MARKET INGESTION SERVICE TEST")
        print("=" * 70)

        # --------------------------------------------------------
        # Test 1: Existing real observation should be detected
        # --------------------------------------------------------

        print("\n1. Testing duplicate protection...")

        result = service.ingest_price(
            market_id=1,
            crop_id=1,
            price=455,
            price_date=date(2026, 9, 14),
            currency="RWF",
            unit="KG",
            source="TEST_INGESTION",
            source_reference="ingestion service test",
            min_price=400,
            max_price=500,
            quality_grade="STANDARD",
        )

        print(result)

        assert result["status"] == "DUPLICATE"

        # --------------------------------------------------------
        # Test 2: Insert a new observation
        # --------------------------------------------------------

        print("\n2. Testing new price ingestion...")

        result = service.ingest_price(
            market_id=1,
            crop_id=1,
            price=470,
            price_date=date(2026, 9, 15),
            currency="RWF",
            unit="KG",
            source="TEST_INGESTION",
            source_reference="FarmIQ ingestion service test",
            min_price=450,
            max_price=490,
            quality_grade="STANDARD",
        )

        print(result)

        assert result["status"] == "INSERTED"

        inserted_price_id = result["price_id"]

        # --------------------------------------------------------
        # Test 3: Same record again
        # --------------------------------------------------------

        print("\n3. Testing duplicate detection on newly inserted price...")

        result = service.ingest_price(
            market_id=1,
            crop_id=1,
            price=470,
            price_date=date(2026, 9, 15),
            currency="RWF",
            unit="KG",
            source="TEST_INGESTION",
            source_reference="FarmIQ ingestion service test",
            min_price=450,
            max_price=490,
            quality_grade="STANDARD",
        )

        print(result)

        assert result["status"] == "DUPLICATE"
        assert result["price_id"] == inserted_price_id

        # --------------------------------------------------------
        # Test 4: Batch ingestion
        # --------------------------------------------------------

        print("\n4. Testing batch ingestion...")

        records = [
            {
                "market_id": 1,
                "crop_id": 1,
                "price": 475,
                "price_date": date(2026, 9, 16),
                "currency": "RWF",
                "unit": "KG",
                "source": "TEST_BATCH",
                "source_reference": "Batch test 1",
                "min_price": 450,
                "max_price": 500,
                "quality_grade": "STANDARD",
            },
            {
                "market_id": 1,
                "crop_id": 1,
                "price": 480,
                "price_date": date(2026, 9, 17),
                "currency": "RWF",
                "unit": "KG",
                "source": "TEST_BATCH",
                "source_reference": "Batch test 2",
                "min_price": 450,
                "max_price": 500,
                "quality_grade": "STANDARD",
            },
            {
                "market_id": 1,
                "crop_id": 1,
                "price": 485,
                "price_date": date(2026, 9, 18),
                "currency": "RWF",
                "unit": "KG",
                "source": "TEST_BATCH",
                "source_reference": "Batch test 3",
                "min_price": 450,
                "max_price": 500,
                "quality_grade": "STANDARD",
            },
        ]

        batch_result = service.ingest_prices(records)

        print(batch_result)

        assert batch_result["inserted"] == 3
        assert batch_result["failed"] == 0

        print("\n" + "=" * 70)
        print("ALL MARKET INGESTION TESTS PASSED")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()
