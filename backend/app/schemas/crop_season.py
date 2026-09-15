from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CropSeasonCreate(BaseModel):
    field_id: int
    crop_id: int
    variety: str | None = Field(default=None, max_length=150)
    area_hectares: Decimal = Field(gt=0)
    planting_date: datetime | None = None
    expected_harvest_date: datetime | None = None
    actual_harvest_date: datetime | None = None
    expected_yield_kg: Decimal | None = Field(default=None, ge=0)
    actual_yield_kg: Decimal | None = Field(default=None, ge=0)
    status: str = Field(default="PLANNED", max_length=30)
    notes: str | None = None


class CropSeasonUpdate(BaseModel):
    field_id: int | None = None
    crop_id: int | None = None
    variety: str | None = Field(default=None, max_length=150)
    area_hectares: Decimal | None = Field(default=None, gt=0)
    planting_date: datetime | None = None
    expected_harvest_date: datetime | None = None
    actual_harvest_date: datetime | None = None
    expected_yield_kg: Decimal | None = Field(default=None, ge=0)
    actual_yield_kg: Decimal | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, max_length=30)
    notes: str | None = None


class CropSeasonResponse(BaseModel):
    id: int
    field_id: int
    crop_id: int
    variety: str | None
    area_hectares: Decimal
    planting_date: datetime | None
    expected_harvest_date: datetime | None
    actual_harvest_date: datetime | None
    expected_yield_kg: Decimal | None
    actual_yield_kg: Decimal | None
    status: str
    notes: str | None

    model_config = ConfigDict(from_attributes=True)
