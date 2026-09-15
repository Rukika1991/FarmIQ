from fastapi import FastAPI

from app.api.v1.router import api_router


app = FastAPI(
    title="FarmIQ API",
    description="AI-Powered Agriculture Intelligence Platform",
    version="1.0.0",
)


app.include_router(api_router)


@app.get("/")
def root():
    return {
        "application": "FarmIQ",
        "message": "FarmIQ API is running",
        "version": "1.0.0",
    }


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "application": "FarmIQ",
    }
