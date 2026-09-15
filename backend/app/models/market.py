from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ============================================================
# MARKET
# ============================================================

class Market(Base):
    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    region: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    market_level: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    # LOCAL
    # REGIONAL
    # INTERNATIONAL

    market_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    # FARM_GATE
    # WHOLESALE
    # RETAIL
    # EXPORT
    # COMMODITY_EXCHANGE
    # OTHER

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )

    source: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    prices: Mapped[list["MarketPrice"]] = relationship(
        back_populates="market",
        cascade="all, delete-orphan",
    )

    forecasts: Mapped[list["PriceForecast"]] = relationship(
        back_populates="market",
        cascade="all, delete-orphan",
    )


# ============================================================
# MARKET PRICE
# ============================================================

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    market_id: Mapped[int] = mapped_column(
        ForeignKey("markets.id"),
        nullable=False,
    )

    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id"),
        nullable=False,
    )

    price_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    # KG
    # TONNE
    # BAG
    # LITRE
    # PIECE
    # OTHER

    min_price: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 4),
        nullable=True,
    )

    max_price: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 4),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    source_reference: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    quality_grade: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    market: Mapped["Market"] = relationship(
        back_populates="prices",
    )

    crop: Mapped["Crop"] = relationship()


# ============================================================
# PRICE FORECAST
# ============================================================

class PriceForecast(Base):
    __tablename__ = "price_forecasts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    market_id: Mapped[int] = mapped_column(
        ForeignKey("markets.id"),
        nullable=False,
    )

    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id"),
        nullable=False,
    )

    forecast_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    predicted_price: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        nullable=False,
    )

    lower_price: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 4),
        nullable=True,
    )

    upper_price: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 4),
        nullable=True,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    model_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    source: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    market: Mapped["Market"] = relationship(
        back_populates="forecasts",
    )

    crop: Mapped["Crop"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "market_id",
            "crop_id",
            "forecast_date",
            "model_version",
            name="uq_price_forecast_market_crop_date_model",
        ),
    )
