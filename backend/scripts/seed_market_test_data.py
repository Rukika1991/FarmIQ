from datetime import date, timedelta
import random

from app.core.database import SessionLocal
from app.models.market import Market, MarketPrice
from app.models.models import Crop


# ============================================================
# FARM IQ MARKET TEST DATA
# ============================================================

MARKET_ID = 1
CROP_ID = 1

TEST_SOURCE = "TEST_DATA"
TEST_QUALITY = "STANDARD"

START_DATE = date(2026, 8, 16)
END_DATE = date(2026, 9, 13)

START_PRICE = 420.0
END_PRICE = 452.0

RANDOM_SEED = 42


def generate_test_prices():
    """
    Generate a simple upward-trending historical price series.

    IMPORTANT:
    These are development/test observations only.
    They are never presented as real market data.
    """

    random.seed(RANDOM_SEED)

    total_days = (
        END_DATE - START_DATE
    ).days + 1

    if total_days <= 0:
        raise ValueError(
            "END_DATE must be on or after START_DATE."
        )

    daily_trend = (
        END_PRICE - START_PRICE
    ) / (total_days - 1)

    records = []

    for index in range(total_days):
        current_date = (
            START_DATE
            + timedelta(days=index)
        )

        base_price = (
            START_PRICE
            + daily_trend * index
        )

        variation = random.uniform(
            -3.0,
            3.0,
        )

        price = round(
            base_price + variation,
            2,
        )

        records.append(
            {
                "price_date": current_date,
                "price": price,
            }
        )

    return records


def main():
    db = SessionLocal()

    try:
        print("\n========================================")
        print("FARMIQ MARKET TEST DATA")
        print("========================================")

        # ----------------------------------------------------
        # 1. Validate market
        # ----------------------------------------------------

        market = (
            db.query(Market)
            .filter(Market.id == MARKET_ID)
            .first()
        )

        if not market:
            raise ValueError(
                f"Market ID {MARKET_ID} was not found."
            )

        print(
            f"Market: {market.name} "
            f"(ID {market.id})"
        )

        # ----------------------------------------------------
        # 2. Validate crop
        # ----------------------------------------------------

        crop = (
            db.query(Crop)
            .filter(Crop.id == CROP_ID)
            .first()
        )

        if not crop:
            raise ValueError(
                f"Crop ID {CROP_ID} was not found."
            )

        print(
            f"Crop: {crop.name} "
            f"(ID {crop.id})"
        )

        # ----------------------------------------------------
        # 3. Generate test observations
        # ----------------------------------------------------

        test_records = generate_test_prices()

        inserted = 0
        skipped = 0

        # ----------------------------------------------------
        # 4. Insert without touching real data
        # ----------------------------------------------------

        for record in test_records:

            existing = (
                db.query(MarketPrice)
                .filter(
                    MarketPrice.market_id
                    == MARKET_ID,
                    MarketPrice.crop_id
                    == CROP_ID,
                    MarketPrice.price_date
                    == record["price_date"],
                    MarketPrice.unit
                    == "KG",
                    MarketPrice.quality_grade
                    == TEST_QUALITY,
                )
                .first()
            )

            if existing:
                skipped += 1
                continue

            market_price = MarketPrice(
                market_id=MARKET_ID,
                crop_id=CROP_ID,
                price_date=record["price_date"],
                price=record["price"],
                currency="RWF",
                unit="KG",
                min_price=round(
                    record["price"] - 10,
                    2,
                ),
                max_price=round(
                    record["price"] + 10,
                    2,
                ),
                source=TEST_SOURCE,
                source_reference=(
                    "FarmIQ forecasting development dataset"
                ),
                quality_grade=TEST_QUALITY,
                notes=(
                    "Synthetic development data. "
                    "Not a real market observation."
                ),
            )

            db.add(market_price)
            inserted += 1

        db.commit()

        # ----------------------------------------------------
        # 5. Summary
        # ----------------------------------------------------

        print("\n----------------------------------------")
        print("RESULT")
        print("----------------------------------------")

        print(
            f"Generated observations: {len(test_records)}"
        )
        print(
            f"Inserted observations:  {inserted}"
        )
        print(
            f"Skipped duplicates:     {skipped}"
        )

        print("\nTest data period:")
        print(
            f"{START_DATE} → {END_DATE}"
        )

        print("\nSource:")
        print(TEST_SOURCE)

        print(
            "\nThe existing real 2026-09-14 "
            "observation was NOT modified."
        )

        print("\n========================================")
        print("TEST DATA SEED COMPLETE")
        print("========================================\n")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
