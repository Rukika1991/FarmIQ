from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.market import Market, MarketPrice, PriceForecast
from app.models.models import Crop
from app.schemas.market import (
    MarketCreate,
    MarketUpdate,
    MarketPriceCreate,
    MarketPriceUpdate,
    PriceForecastCreate,
)


# ============================================================
# MARKET SERVICES
# ============================================================

def create_market(
    db: Session,
    market_data: MarketCreate,
):
    existing_market = (
        db.query(Market)
        .filter(
            Market.name.ilike(market_data.name.strip()),
            Market.country.ilike(market_data.country.strip()),
        )
        .first()
    )

    if existing_market:
        raise HTTPException(
            status_code=409,
            detail="A market with this name already exists in this country.",
        )

    market = Market(
        name=market_data.name.strip(),
        country=market_data.country.strip(),
        region=market_data.region,
        district=market_data.district,
        city=market_data.city,
        latitude=market_data.latitude,
        longitude=market_data.longitude,
        market_level=market_data.market_level,
        market_type=market_data.market_type,
        currency=market_data.currency,
        is_active=market_data.is_active,
        source=market_data.source,
        notes=market_data.notes,
    )

    try:
        db.add(market)
        db.commit()
        db.refresh(market)
        return market
    except Exception:
        db.rollback()
        raise


def get_markets(
    db: Session,
    active_only: bool = False,
    market_level: str | None = None,
):
    query = db.query(Market)

    if active_only:
        query = query.filter(
            Market.is_active.is_(True)
        )

    if market_level:
        query = query.filter(
            Market.market_level == market_level
        )

    return (
        query
        .order_by(Market.name)
        .all()
    )


def get_market(
    db: Session,
    market_id: int,
):
    market = (
        db.query(Market)
        .filter(Market.id == market_id)
        .first()
    )

    if not market:
        raise HTTPException(
            status_code=404,
            detail="Market not found.",
        )

    return market


def update_market(
    db: Session,
    market_id: int,
    market_data: MarketUpdate,
):
    market = get_market(db, market_id)

    update_data = market_data.model_dump(
        exclude_unset=True
    )

    if "name" in update_data:
        new_name = update_data["name"].strip()

        country_for_check = update_data.get(
            "country",
            market.country,
        )

        existing_market = (
            db.query(Market)
            .filter(
                Market.name.ilike(new_name),
                Market.country.ilike(
                    country_for_check.strip()
                ),
                Market.id != market_id,
            )
            .first()
        )

        if existing_market:
            raise HTTPException(
                status_code=409,
                detail="A market with this name already exists in this country.",
            )

        update_data["name"] = new_name

    if "country" in update_data:
        update_data["country"] = (
            update_data["country"].strip()
        )

    for key, value in update_data.items():
        setattr(market, key, value)

    try:
        db.commit()
        db.refresh(market)
        return market
    except Exception:
        db.rollback()
        raise


def delete_market(
    db: Session,
    market_id: int,
):
    market = get_market(db, market_id)

    try:
        db.delete(market)
        db.commit()

        return {
            "message": "Market deleted successfully.",
            "market_id": market_id,
        }

    except Exception:
        db.rollback()
        raise


# ============================================================
# MARKET PRICE SERVICES
# ============================================================

def create_market_price(
    db: Session,
    price_data: MarketPriceCreate,
):
    # ---------------------------------------------------------
    # 1. Validate market
    # ---------------------------------------------------------

    market = (
        db.query(Market)
        .filter(
            Market.id == price_data.market_id
        )
        .first()
    )

    if not market:
        raise HTTPException(
            status_code=404,
            detail="Market not found.",
        )

    # ---------------------------------------------------------
    # 2. Validate crop
    # ---------------------------------------------------------

    crop = (
        db.query(Crop)
        .filter(
            Crop.id == price_data.crop_id
        )
        .first()
    )

    if not crop:
        raise HTTPException(
            status_code=404,
            detail="Crop not found.",
        )

    # ---------------------------------------------------------
    # 3. Prevent duplicate price observation
    #
    # Same:
    #   market
    #   crop
    #   date
    #   unit
    #   quality grade
    # ---------------------------------------------------------

    existing_price_query = (
        db.query(MarketPrice)
        .filter(
            MarketPrice.market_id
            == price_data.market_id,
            MarketPrice.crop_id
            == price_data.crop_id,
            MarketPrice.price_date
            == price_data.price_date,
            MarketPrice.unit
            == price_data.unit,
        )
    )

    # Quality grade is nullable, so handle NULL correctly.
    if price_data.quality_grade is None:
        existing_price_query = (
            existing_price_query.filter(
                MarketPrice.quality_grade.is_(None)
            )
        )
    else:
        existing_price_query = (
            existing_price_query.filter(
                MarketPrice.quality_grade
                == price_data.quality_grade
            )
        )

    existing_price = (
        existing_price_query.first()
    )

    if existing_price:
        raise HTTPException(
            status_code=409,
            detail=(
                "A market price already exists for "
                "this market, crop, date, unit, and "
                "quality grade."
            ),
        )

    # ---------------------------------------------------------
    # 4. Create actual market price
    # ---------------------------------------------------------

    market_price = MarketPrice(
        market_id=price_data.market_id,
        crop_id=price_data.crop_id,
        price_date=price_data.price_date,
        price=price_data.price,
        currency=price_data.currency,
        unit=price_data.unit,
        min_price=price_data.min_price,
        max_price=price_data.max_price,
        source=price_data.source,
        source_reference=price_data.source_reference,
        quality_grade=price_data.quality_grade,
        notes=price_data.notes,
    )

    try:
        db.add(market_price)
        db.commit()
        db.refresh(market_price)
        return market_price

    except Exception:
        db.rollback()
        raise


def get_market_prices(
    db: Session,
    market_id: int | None = None,
    crop_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    query = db.query(MarketPrice)

    if market_id is not None:
        query = query.filter(
            MarketPrice.market_id == market_id
        )

    if crop_id is not None:
        query = query.filter(
            MarketPrice.crop_id == crop_id
        )

    if start_date is not None:
        query = query.filter(
            MarketPrice.price_date >= start_date
        )

    if end_date is not None:
        query = query.filter(
            MarketPrice.price_date <= end_date
        )

    return (
        query
        .order_by(
            MarketPrice.price_date.desc()
        )
        .all()
    )


def get_market_price(
    db: Session,
    price_id: int,
):
    price = (
        db.query(MarketPrice)
        .filter(
            MarketPrice.id == price_id
        )
        .first()
    )

    if not price:
        raise HTTPException(
            status_code=404,
            detail="Market price not found.",
        )

    return price


def update_market_price(
    db: Session,
    price_id: int,
    price_data: MarketPriceUpdate,
):
    market_price = get_market_price(
        db,
        price_id,
    )

    update_data = price_data.model_dump(
        exclude_unset=True
    )

    # ---------------------------------------------------------
    # Validate market if being changed
    # ---------------------------------------------------------

    if "market_id" in update_data:
        market = (
            db.query(Market)
            .filter(
                Market.id
                == update_data["market_id"]
            )
            .first()
        )

        if not market:
            raise HTTPException(
                status_code=404,
                detail="Market not found.",
            )

    # ---------------------------------------------------------
    # Validate crop if being changed
    # ---------------------------------------------------------

    if "crop_id" in update_data:
        crop = (
            db.query(Crop)
            .filter(
                Crop.id
                == update_data["crop_id"]
            )
            .first()
        )

        if not crop:
            raise HTTPException(
                status_code=404,
                detail="Crop not found.",
            )

    # ---------------------------------------------------------
    # Check for duplicate after update
    # ---------------------------------------------------------

    final_market_id = update_data.get(
        "market_id",
        market_price.market_id,
    )

    final_crop_id = update_data.get(
        "crop_id",
        market_price.crop_id,
    )

    final_price_date = update_data.get(
        "price_date",
        market_price.price_date,
    )

    final_unit = update_data.get(
        "unit",
        market_price.unit,
    )

    final_quality_grade = update_data.get(
        "quality_grade",
        market_price.quality_grade,
    )

    duplicate_query = (
        db.query(MarketPrice)
        .filter(
            MarketPrice.market_id
            == final_market_id,
            MarketPrice.crop_id
            == final_crop_id,
            MarketPrice.price_date
            == final_price_date,
            MarketPrice.unit
            == final_unit,
            MarketPrice.id != price_id,
        )
    )

    if final_quality_grade is None:
        duplicate_query = (
            duplicate_query.filter(
                MarketPrice.quality_grade.is_(None)
            )
        )
    else:
        duplicate_query = (
            duplicate_query.filter(
                MarketPrice.quality_grade
                == final_quality_grade
            )
        )

    if duplicate_query.first():
        raise HTTPException(
            status_code=409,
            detail=(
                "The update would create a duplicate "
                "market price observation."
            ),
        )

    # ---------------------------------------------------------
    # Apply updates
    # ---------------------------------------------------------

    for key, value in update_data.items():
        setattr(
            market_price,
            key,
            value,
        )

    try:
        db.commit()
        db.refresh(market_price)
        return market_price

    except Exception:
        db.rollback()
        raise


def delete_market_price(
    db: Session,
    price_id: int,
):
    market_price = get_market_price(
        db,
        price_id,
    )

    try:
        db.delete(market_price)
        db.commit()

        return {
            "message": "Market price deleted successfully.",
            "price_id": price_id,
        }

    except Exception:
        db.rollback()
        raise


# ============================================================
# PRICE FORECAST SERVICES
# ============================================================

def create_price_forecast(
    db: Session,
    forecast_data: PriceForecastCreate,
):
    market = (
        db.query(Market)
        .filter(
            Market.id == forecast_data.market_id
        )
        .first()
    )

    if not market:
        raise HTTPException(
            status_code=404,
            detail="Market not found.",
        )

    crop = (
        db.query(Crop)
        .filter(
            Crop.id == forecast_data.crop_id
        )
        .first()
    )

    if not crop:
        raise HTTPException(
            status_code=404,
            detail="Crop not found.",
        )

    forecast = PriceForecast(
        market_id=forecast_data.market_id,
        crop_id=forecast_data.crop_id,
        forecast_date=forecast_data.forecast_date,
        predicted_price=forecast_data.predicted_price,
        lower_price=forecast_data.lower_price,
        upper_price=forecast_data.upper_price,
        currency=forecast_data.currency,
        unit=forecast_data.unit,
        confidence=forecast_data.confidence,
        model_name=forecast_data.model_name,
        model_version=forecast_data.model_version,
        source=forecast_data.source,
        notes=forecast_data.notes,
    )

    try:
        db.add(forecast)
        db.commit()
        db.refresh(forecast)
        return forecast

    except Exception:
        db.rollback()
        raise


def get_price_forecasts(
    db: Session,
    market_id: int | None = None,
    crop_id: int | None = None,
):
    query = db.query(PriceForecast)

    if market_id is not None:
        query = query.filter(
            PriceForecast.market_id == market_id
        )

    if crop_id is not None:
        query = query.filter(
            PriceForecast.crop_id == crop_id
        )

    return (
        query
        .order_by(
            PriceForecast.forecast_date
        )
        .all()
    )


def get_price_forecast(
    db: Session,
    forecast_id: int,
):
    forecast = (
        db.query(PriceForecast)
        .filter(
            PriceForecast.id == forecast_id
        )
        .first()
    )

    if not forecast:
        raise HTTPException(
            status_code=404,
            detail="Price forecast not found.",
        )

    return forecast
