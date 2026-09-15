from pydantic import BaseModel, ConfigDict, Field


class CropCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    scientific_name: str | None = Field(
        default=None,
        max_length=150,
    )

    description: str | None = None

    is_active: bool = True


class CropUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    scientific_name: str | None = Field(
        default=None,
        max_length=150,
    )

    description: str | None = None

    is_active: bool | None = None


class CropResponse(BaseModel):
    id: int
    name: str
    scientific_name: str | None
    description: str | None
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )
