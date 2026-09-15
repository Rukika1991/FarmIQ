from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SoilProfileCreate(BaseModel):
    field_id: int

    source: str = Field(
        ...,
        description="Source of soil information: LABORATORY or LOCATION_ESTIMATE",
    )

    ph: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("14"),
    )

    nitrogen: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
    )

    phosphorus: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
    )

    potassium: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
    )

    organic_carbon: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
    )

    texture: str | None = Field(
        default=None,
        max_length=100,
    )

    soil_depth_cm: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
    )

    drainage: str | None = Field(
        default=None,
        max_length=100,
    )

    confidence: str = Field(
        default="MEDIUM",
        max_length=30,
    )

    test_date: datetime | None = None

    is_active: bool = True

    notes: str | None = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        value = value.upper()

        allowed = {
            "LABORATORY",
            "LOCATION_ESTIMATE",
        }

        if value not in allowed:
            raise ValueError(
                "source must be LABORATORY or LOCATION_ESTIMATE"
            )

        return value

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: str) -> str:
        value = value.upper()

        allowed = {
            "HIGH",
            "MEDIUM",
            "LOW",
        }

        if value not in allowed:
            raise ValueError(
                "confidence must be HIGH, MEDIUM, or LOW"
            )

        return value


class SoilProfileUpdate(BaseModel):
    ph: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        le=Decimal("14"),
    )

    nitrogen: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
    )

    phosphorus: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
    )

    potassium: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
    )

    organic_carbon: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
    )

    texture: str | None = Field(
        default=None,
        max_length=100,
    )

    soil_depth_cm: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
    )

    drainage: str | None = Field(
        default=None,
        max_length=100,
    )

    confidence: str | None = Field(
        default=None,
        max_length=30,
    )

    test_date: datetime | None = None

    is_active: bool | None = None

    notes: str | None = None

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.upper()

        allowed = {
            "HIGH",
            "MEDIUM",
            "LOW",
        }

        if value not in allowed:
            raise ValueError(
                "confidence must be HIGH, MEDIUM, or LOW"
            )

        return value


class SoilProfileResponse(BaseModel):
    id: int
    field_id: int
    source: str
    ph: Decimal | None
    nitrogen: Decimal | None
    phosphorus: Decimal | None
    potassium: Decimal | None
    organic_carbon: Decimal | None
    texture: str | None
    soil_depth_cm: Decimal | None
    drainage: str | None
    confidence: str
    test_date: datetime | None
    is_active: bool
    notes: str | None

    model_config = ConfigDict(from_attributes=True)
