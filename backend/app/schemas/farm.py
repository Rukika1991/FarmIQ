from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FarmCreate(BaseModel):
    farmer_id: int
    name: str = Field(..., min_length=2, max_length=150)
    district: str = Field(..., min_length=2, max_length=100)
    sector: str | None = Field(default=None, max_length=100)
    village: str | None = Field(default=None, max_length=100)

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


class FarmUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    district: str | None = Field(default=None, min_length=2, max_length=100)
    sector: str | None = Field(default=None, max_length=100)
    village: str | None = Field(default=None, max_length=100)

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


class FarmResponse(BaseModel):
    id: int
    farmer_id: int
    name: str
    district: str
    sector: str | None
    village: str | None
    latitude: Decimal | None
    longitude: Decimal | None

    model_config = ConfigDict(from_attributes=True)
