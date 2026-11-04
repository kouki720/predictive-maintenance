
from fastapi import FastAPI

from app.routes.simulation import router as simulation_router


app = FastAPI(
    title="Industrial IoT Sensor Simulator",
    description=(
        "API for generating synthetic industrial sensor "
        "measurements from historical NORMAL operating data."
    ),
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "application": "Industrial IoT Sensor Simulator",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


app.include_router(simulation_router)
