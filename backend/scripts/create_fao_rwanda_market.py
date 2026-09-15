
"""
FarmIQ - Create Rwanda National FAOSTAT Producer Price Market

This script creates the destination market for national-level
FAOSTAT producer-price observations.

IMPORTANT:
    - Does NOT insert FAOSTAT price records.
    - Does NOT import FAOSTAT data.
    - Safe to run repeatedly.
    - If the market already exists, it will not create a duplicate.
"""

from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# MAKE BACKEND ROOT IMPORTABLE
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# FARM-IQ IMPORTS
# ============================================================

from sqlalchemy import select

from app.core.database import SessionLocal

from app.core.market_constants import (
    MARKET_LEVEL_NATIONAL,
    MARKET_TYPE_FARM_GATE,
)

from app.models.market import Market


# ============================================================
# CONFIGURATION
# ============================================================

MARKET_NAME = "Rwanda National Producer Price"

COUNTRY = "Rwanda"

MARKET_LEVEL = MARKET_LEVEL_NATIONAL

MARKET_TYPE = MARKET_TYPE_FARM_GATE

CURRENCY = "RWF"

SOURCE = "FAOSTAT"

NOTES = (
    "National-level agricultural producer prices from FAOSTAT. "
    "Represents producer/farm-gate prices at national level. "
    "FAOSTAT item: Potatoes (item code 116). "
    "This market is separate from physical local, regional, "
    "and international markets."
)


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 70)
    print("FARMIQ - CREATE FAOSTAT RWANDA NATIONAL MARKET")
    print("=" * 70)
    print()

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # CHECK FOR EXISTING MARKET
        # ----------------------------------------------------

        existing = db.scalar(
            select(Market).where(
                Market.name == MARKET_NAME,
                Market.country == COUNTRY,
                Market.market_level == MARKET_LEVEL,
                Market.source == SOURCE,
            )
        )

        if existing:

            print("Market already exists.")
            print()

            print(f"ID          : {existing.id}")
            print(f"Name        : {existing.name}")
            print(f"Country     : {existing.country}")
            print(f"Level       : {existing.market_level}")
            print(f"Type        : {existing.market_type}")
            print(f"Currency    : {existing.currency}")
            print(f"Source      : {existing.source}")
            print()

            print("NO NEW MARKET WAS CREATED.")
            print()

            return

        # ----------------------------------------------------
        # CREATE MARKET
        # ----------------------------------------------------

        market = Market(
            name=MARKET_NAME,
            country=COUNTRY,
            region=None,
            district=None,
            city=None,
            latitude=None,
            longitude=None,
            market_level=MARKET_LEVEL,
            market_type=MARKET_TYPE,
            currency=CURRENCY,
            is_active=True,
            source=SOURCE,
            notes=NOTES,
        )

        db.add(market)

        db.commit()

        db.refresh(market)

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        print("Rwanda national FAOSTAT market created successfully.")
        print()

        print(f"ID          : {market.id}")
        print(f"Name        : {market.name}")
        print(f"Country     : {market.country}")
        print(f"Level       : {market.market_level}")
        print(f"Type        : {market.market_type}")
        print(f"Currency    : {market.currency}")
        print(f"Source      : {market.source}")
        print()

        print("IMPORTANT:")
        print("No FAOSTAT price records were inserted.")
        print("Only the destination market record was created.")
        print()

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()