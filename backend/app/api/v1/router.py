from fastapi import APIRouter

from app.api.v1.farmers import router as farmers_router
from app.api.v1.farms import router as farms_router
from app.api.v1.fields import router as fields_router
from app.api.v1.soil import router as soil_router
from app.api.v1.crops import router as crops_router
from app.api.v1.crop_seasons import router as crop_seasons_router
from app.api.v1.weather import router as weather_router
from app.api.v1.market import router as market_router


api_router = APIRouter(
    prefix="/api/v1",
)


api_router.include_router(farmers_router)
api_router.include_router(farms_router)
api_router.include_router(fields_router)
api_router.include_router(soil_router)
api_router.include_router(crops_router)
api_router.include_router(crop_seasons_router)
api_router.include_router(weather_router)
api_router.include_router(market_router)
