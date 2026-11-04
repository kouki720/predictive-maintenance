
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.services.simulation_service import run_simulation


router = APIRouter(
    prefix="/api/simulation",
    tags=["Simulation"],
)


@router.post("/run")
def run_sensor_simulation():

    try:
        return run_simulation(
            current_timestamp=datetime.now()
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
