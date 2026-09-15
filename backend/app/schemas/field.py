from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FieldCreate(BaseModel):
    farm_id: int
    name: str = Field(..., min_length=2, max_length=150)

    area_hectares: Decimal = Field(
        ...,
        gt=Decimal("0"),
        le=Decimal("100000"),
    )

    latitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
    )

    longitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
    )


class FieldUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    area_hectares: Decimal | None = Field(
        default=None,
        gt=Decimal("0"),
        le=Decimal("100000"),
    )

    latitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
    )

    longitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
    )


class FieldResponse(BaseModel):
    id: int
    farm_id: int
    name: str
    area_hectares: Decimal
    latitude: Decimal | None
    longitude: Decimal | None

    model_config = ConfigDict(from_attributes=True)
