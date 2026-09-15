from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.schemas.market import (
    MarketCreate,
    MarketUpdate,
    MarketResponse,
    MarketPriceCreate,
    MarketPriceUpdate,
    MarketPriceResponse,
    PriceForecastCreate,
    PriceForecastResponse,
)

from app.services.market_service import (
    create_market,
    get_markets,
    get_market,
    update_market,
    delete_market,
    create_market_price,
    get_market_prices,
    get_market_price,
    update_market_price,
    delete_market_price,
    create_price_forecast,
    get_price_forecasts,
    get_price_forecast,
)

from app.services.market_forecasting import (
    MarketForecastingService,
)


router = APIRouter(
    prefix="/markets",
    tags=["Market Intelligence"],
)


# ============================================================
# MARKETS
# ============================================================

@router.post(
    "/",
    response_model=MarketResponse,
    status_code=201,
)
def create_market_endpoint(
    market_data: MarketCreate,
    db: Session = Depends(get_db),
):
    return create_market(db, market_data)


@router.get(
    "/",
    response_model=list[MarketResponse],
)
def list_markets_endpoint(
    active_only: bool = Query(
        False,
        description="Return only active markets.",
    ),
    market_level: str | None = Query(
        None,
        description="Filter by LOCAL, REGIONAL, or INTERNATIONAL.",
    ),
    db: Session = Depends(get_db),
):
    return get_markets(
        db=db,
        active_only=active_only,
        market_level=market_level,
    )


# ============================================================
# MARKET PRICES
# ============================================================

@router.post(
    "/prices",
    response_model=MarketPriceResponse,
    status_code=201,
)
def create_market_price_endpoint(
    price_data: MarketPriceCreate,
    db: Session = Depends(get_db),
):
    return create_market_price(
        db,
        price_data,
    )


@router.get(
    "/prices",
    response_model=list[MarketPriceResponse],
)
def list_market_prices_endpoint(
    market_id: int | None = Query(
        None,
        description="Filter by market.",
    ),
    crop_id: int | None = Query(
        None,
        description="Filter by crop.",
    ),
    start_date: datetime | None = Query(
        None,
        description="Return prices from this date/time onward.",
    ),
    end_date: datetime | None = Query(
        None,
        description="Return prices up to this date/time.",
    ),
    db: Session = Depends(get_db),
):
    return get_market_prices(
        db=db,
        market_id=market_id,
        crop_id=crop_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/prices/{price_id}",
    response_model=MarketPriceResponse,
)
def get_market_price_endpoint(
    price_id: int,
    db: Session = Depends(get_db),
):
    return get_market_price(
        db,
        price_id,
    )


@router.put(
    "/prices/{price_id}",
    response_model=MarketPriceResponse,
)
def update_market_price_endpoint(
    price_id: int,
    price_data: MarketPriceUpdate,
    db: Session = Depends(get_db),
):
    return update_market_price(
        db,
        price_id,
        price_data,
    )


@router.delete(
    "/prices/{price_id}",
)
def delete_market_price_endpoint(
    price_id: int,
    db: Session = Depends(get_db),
):
    return delete_market_price(
        db,
        price_id,
    )


# ============================================================
# PRICE FORECASTING
# ============================================================

@router.get(
    "/forecasts/predict",
)
def predict_market_price_endpoint(
    market_id: int = Query(
        ...,
        description="Market to forecast.",
    ),
    crop_id: int = Query(
        ...,
        description="Crop to forecast.",
    ),
    forecast_days: int = Query(
        7,
        ge=1,
        le=365,
        description="Number of days into the future.",
    ),
    lookback_days: int = Query(
        30,
        ge=7,
        le=3650,
        description="Number of historical days to use.",
    ),
    db: Session = Depends(get_db),
):
    forecasting_service = MarketForecastingService(db)

    return forecasting_service.forecast_price(
        market_id=market_id,
        crop_id=crop_id,
        forecast_days=forecast_days,
        lookback_days=lookback_days,
    )


# ============================================================
# SAVED PRICE FORECASTS
# ============================================================

@router.post(
    "/forecasts",
    response_model=PriceForecastResponse,
    status_code=201,
)
def create_price_forecast_endpoint(
    forecast_data: PriceForecastCreate,
    db: Session = Depends(get_db),
):
    return create_price_forecast(
        db,
        forecast_data,
    )


@router.get(
    "/forecasts",
    response_model=list[PriceForecastResponse],
)
def list_price_forecasts_endpoint(
    market_id: int | None = Query(
        None,
        description="Filter by market.",
    ),
    crop_id: int | None = Query(
        None,
        description="Filter by crop.",
    ),
    db: Session = Depends(get_db),
):
    return get_price_forecasts(
        db=db,
        market_id=market_id,
        crop_id=crop_id,
    )


@router.get(
    "/forecasts/{forecast_id}",
    response_model=PriceForecastResponse,
)
def get_price_forecast_endpoint(
    forecast_id: int,
    db: Session = Depends(get_db),
):
    return get_price_forecast(
        db,
        forecast_id,
    )


# ============================================================
# MARKET BY ID
# ============================================================

@router.get(
    "/{market_id}",
    response_model=MarketResponse,
)
def get_market_endpoint(
    market_id: int,
    db: Session = Depends(get_db),
):
    return get_market(
        db,
        market_id,
    )


@router.put(
    "/{market_id}",
    response_model=MarketResponse,
)
def update_market_endpoint(
    market_id: int,
    market_data: MarketUpdate,
    db: Session = Depends(get_db),
):
    return update_market(
        db,
        market_id,
        market_data,
    )


@router.delete(
    "/{market_id}",
)
def delete_market_endpoint(
    market_id: int,
    db: Session = Depends(get_db),
):
    return delete_market(
        db,
        market_id,
    )