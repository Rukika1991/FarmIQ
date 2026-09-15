from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# MARKET
# ============================================================

class MarketCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    country: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    region: str | None = Field(
        default=None,
        max_length=100,
    )

    district: str | None = Field(
        default=None,
        max_length=100,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    latitude: Decimal | None = None
    longitude: Decimal | None = None

    market_level: str = Field(
        ...,
        max_length=30,
    )

    market_type: str | None = Field(
        default=None,
        max_length=50,
    )

    currency: str = Field(
        ...,
        min_length=3,
        max_length=10,
    )

    is_active: bool = True

    source: str | None = Field(
        default=None,
        max_length=150,
    )

    notes: str | None = None


class MarketUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    country: str | None = Field(
        default=None,
        max_length=100,
    )

    region: str | None = Field(
        default=None,
        max_length=100,
    )

    district: str | None = Field(
        default=None,
        max_length=100,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    latitude: Decimal | None = None
    longitude: Decimal | None = None

    market_level: str | None = Field(
        default=None,
        max_length=30,
    )

    market_type: str | None = Field(
        default=None,
        max_length=50,
    )

    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=10,
    )

    is_active: bool | None = None

    source: str | None = Field(
        default=None,
        max_length=150,
    )

    notes: str | None = None


class MarketResponse(BaseModel):
    id: int
    name: str
    country: str
    region: str | None
    district: str | None
    city: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    market_level: str
    market_type: str | None
    currency: str
    is_active: bool
    source: str | None
    notes: str | None

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# MARKET PRICE
# ============================================================

class MarketPriceCreate(BaseModel):
    market_id: int
    crop_id: int

    price_date: datetime

    price: Decimal = Field(
        ...,
        gt=0,
    )

    currency: str = Field(
        ...,
        min_length=3,
        max_length=10,
    )

    unit: str = Field(
        ...,
        min_length=1,
        max_length=30,
    )

    min_price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    max_price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    source: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    source_reference: str | None = Field(
        default=None,
        max_length=500,
    )

    quality_grade: str | None = Field(
        default=None,
        max_length=100,
    )

    notes: str | None = None


class MarketPriceUpdate(BaseModel):
    market_id: int | None = None
    crop_id: int | None = None

    price_date: datetime | None = None

    price: Decimal | None = Field(
        default=None,
        gt=0,
    )

    currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=10,
    )

    unit: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    min_price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    max_price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    source: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    source_reference: str | None = Field(
        default=None,
        max_length=500,
    )

    quality_grade: str | None = Field(
        default=None,
        max_length=100,
    )

    notes: str | None = None


class MarketPriceResponse(BaseModel):
    id: int
    market_id: int
    crop_id: int
    price_date: datetime
    price: Decimal
    currency: str
    unit: str
    min_price: Decimal | None
    max_price: Decimal | None
    source: str
    source_reference: str | None
    quality_grade: str | None
    notes: str | None

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# PRICE FORECAST
# ============================================================

class PriceForecastCreate(BaseModel):
    market_id: int
    crop_id: int

    forecast_date: datetime

    predicted_price: Decimal = Field(
        ...,
        gt=0,
    )

    lower_price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    upper_price: Decimal | None = Field(
        default=None,
        ge=0,
    )

    currency: str = Field(
        ...,
        min_length=3,
        max_length=10,
    )

    unit: str = Field(
        ...,
        min_length=1,
        max_length=30,
    )

    confidence: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    model_name: str | None = Field(
        default=None,
        max_length=100,
    )

    model_version: str | None = Field(
        default=None,
        max_length=50,
    )

    source: str | None = Field(
        default=None,
        max_length=150,
    )

    notes: str | None = None


class PriceForecastResponse(BaseModel):
    id: int
    market_id: int
    crop_id: int
    forecast_date: datetime
    predicted_price: Decimal
    lower_price: Decimal | None
    upper_price: Decimal | None
    currency: str
    unit: str
    confidence: Decimal | None
    model_name: str | None
    model_version: str | None
    generated_at: datetime
    source: str | None
    notes: str | None

    model_config = ConfigDict(
        from_attributes=True
    )
