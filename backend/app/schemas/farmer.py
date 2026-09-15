from pydantic import BaseModel, ConfigDict, EmailStr


class FarmerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None


class FarmerResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
