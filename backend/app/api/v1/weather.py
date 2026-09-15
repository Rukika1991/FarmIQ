from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.weather import (
    CurrentWeatherResponse,
    WeatherForecastResponse,
    WeatherObservationResponse,
    WeatherRiskResponse,
)
from app.services.weather.weather_service import WeatherService


router = APIRouter(
    prefix="/weather",
    tags=["Weather Intelligence"],
)


# ============================================================
# CURRENT WEATHER
# ============================================================

@router.get(
    "/fields/{field_id}/current",
    response_model=CurrentWeatherResponse,
)
def get_current_weather(
    field_id: int,
    db: Session = Depends(get_db),
):
    service = WeatherService(db)

    try:
        return service.get_current_weather(
            field_id=field_id,
            save=True,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )


# ============================================================
# FORECAST
# ============================================================

@router.get(
    "/fields/{field_id}/forecast",
    response_model=list[WeatherForecastResponse],
)
def get_forecast(
    field_id: int,
    days: int = Query(
        default=7,
        ge=1,
        le=16,
    ),
    db: Session = Depends(get_db),
):
    service = WeatherService(db)

    try:
        return service.get_forecast(
            field_id=field_id,
            forecast_days=days,
            save=True,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )


# ============================================================
# SAVED OBSERVATIONS
# ============================================================

@router.get(
    "/fields/{field_id}/observations",
    response_model=list[WeatherObservationResponse],
)
def get_saved_observations(
    field_id: int,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
):
    service = WeatherService(db)

    try:
        return service.get_saved_observations(
            field_id=field_id,
            limit=limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ============================================================
# SAVED FORECASTS
# ============================================================

@router.get(
    "/fields/{field_id}/saved-forecasts",
    response_model=list[WeatherForecastResponse],
)
def get_saved_forecasts(
    field_id: int,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
):
    service = WeatherService(db)

    try:
        return service.get_saved_forecasts(
            field_id=field_id,
            limit=limit,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# ============================================================
# HISTORICAL WEATHER
# ============================================================

@router.get(
    "/fields/{field_id}/history",
)
def get_historical_weather(
    field_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    service = WeatherService(db)

    try:
        return service.get_historical_weather(
            field_id=field_id,
            start_date=start_date,
            end_date=end_date,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )


# ============================================================
# WEATHER INTELLIGENCE
# ============================================================

@router.get(
    "/fields/{field_id}/intelligence",
    response_model=WeatherRiskResponse,
)
def get_weather_intelligence(
    field_id: int,
    days: int = Query(
        default=7,
        ge=1,
        le=16,
    ),
    db: Session = Depends(get_db),
):
    """
    Generate agriculture-focused weather intelligence
    for a field using:

    - weather forecast
    - active crop season
    - crop information
    - FarmIQ agricultural risk rules
    """

    service = WeatherService(db)

    try:
        return service.get_weather_intelligence(
            field_id=field_id,
            forecast_days=days,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )
