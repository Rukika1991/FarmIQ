
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ============================================================
# USER
# ============================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        default="FARMER",
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    farmer: Mapped["Farmer | None"] = relationship(
        back_populates="user",
        uselist=False,
    )


# ============================================================
# FARMER
# ============================================================

class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="farmer",
    )

    farms: Mapped[list["Farm"]] = relationship(
        back_populates="farmer",
        cascade="all, delete-orphan",
    )


# ============================================================
# FARM
# ============================================================

class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    district: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    sector: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    village: Mapped[str | None] = mapped_column(
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

    farmer: Mapped["Farmer"] = relationship(
        back_populates="farms",
    )

    fields: Mapped[list["Field"]] = relationship(
        back_populates="farm",
        cascade="all, delete-orphan",
    )


# ============================================================
# FIELD
# ============================================================

class Field(Base):
    __tablename__ = "fields"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    farm_id: Mapped[int] = mapped_column(
        ForeignKey("farms.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    area_hectares: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    farm: Mapped["Farm"] = relationship(
        back_populates="fields",
    )

    soil_profiles: Mapped[list["SoilProfile"]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
    )

    crop_seasons: Mapped[list["CropSeason"]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
    )

    weather_observations: Mapped[list["WeatherObservation"]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
    )

    weather_forecasts: Mapped[list["WeatherForecast"]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
    )

    weather_alerts: Mapped[list["WeatherAlert"]] = relationship(
        back_populates="field",
        cascade="all, delete-orphan",
    )


# ============================================================
# SOIL PROFILE
# ============================================================

class SoilProfile(Base):
    __tablename__ = "soil_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    field_id: Mapped[int] = mapped_column(
        ForeignKey("fields.id"),
        nullable=False,
    )

    # LABORATORY = priority 1
    # LOCATION_ESTIMATE = priority 2
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    ph: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    nitrogen: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    phosphorus: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    potassium: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )

    organic_carbon: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4),
        nullable=True,
    )

    texture: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    soil_depth_cm: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True,
    )

    drainage: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    confidence: Mapped[str] = mapped_column(
        String(30),
        default="MEDIUM",
        nullable=False,
    )

    test_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    field: Mapped["Field"] = relationship(
        back_populates="soil_profiles",
    )


# ============================================================
# CROP
# ============================================================

class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    scientific_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    crop_seasons: Mapped[list["CropSeason"]] = relationship(
        back_populates="crop",
    )


# ============================================================
# CROP SEASON
# ============================================================

class CropSeason(Base):
    __tablename__ = "crop_seasons"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    field_id: Mapped[int] = mapped_column(
        ForeignKey("fields.id"),
        nullable=False,
    )

    crop_id: Mapped[int] = mapped_column(
        ForeignKey("crops.id"),
        nullable=False,
    )

    variety: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    area_hectares: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
    )

    planting_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    expected_harvest_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    actual_harvest_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    expected_yield_kg: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    actual_yield_kg: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PLANNED",
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    field: Mapped["Field"] = relationship(
        back_populates="crop_seasons",
    )

    crop: Mapped["Crop"] = relationship(
        back_populates="crop_seasons",
    )


# ============================================================
# WEATHER MODEL IMPORTS
# ============================================================

from app.models.weather import (
    WeatherObservation,
    WeatherForecast,
    WeatherAlert,
)

# ============================================================
# DISEASE DETECTION MODEL IMPORTS
# ============================================================

from app.models.disease import DiseaseDetection
