from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# ============================================================
# CURRENT WEATHER
# ============================================================

class CurrentWeatherResponse(BaseModel):
    latitude: float | None
    longitude: float | None
    observed_at: str | None

    temperature_c: float | None
    feels_like_c: float | None
    humidity_percent: float | None
    rainfall_mm: float | None

    wind_speed_kmh: float | None
    wind_direction: int | None
    pressure_hpa: float | None

    weather_code: int | None
    weather_condition: str | None
    source: str


# ============================================================
# FORECAST
# ============================================================

class WeatherForecastResponse(BaseModel):
    id: int | None = None
    field_id: int | None = None

    forecast_date: datetime | str

    temperature_c: Decimal | float | None
    temperature_min_c: Decimal | float | None
    temperature_max_c: Decimal | float | None

    humidity_percent: Decimal | float | None
    rain_probability: Decimal | float | None
    rainfall_mm: Decimal | float | None
    wind_speed_kmh: Decimal | float | None

    weather_condition: str | None
    source: str

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# SAVED OBSERVATION
# ============================================================

class WeatherObservationResponse(BaseModel):
    id: int
    field_id: int

    observed_at: datetime

    temperature_c: Decimal | float | None
    feels_like_c: Decimal | float | None
    humidity_percent: Decimal | float | None
    rainfall_mm: Decimal | float | None

    wind_speed_kmh: Decimal | float | None
    wind_direction: int | None
    pressure_hpa: Decimal | float | None

    weather_condition: str | None
    source: str

    model_config = ConfigDict(
        from_attributes=True
    )
class WeatherRiskResponse(BaseModel):
    risk_level: str
    summary: str
    risks: list[dict]
    recommendations: list[str]
