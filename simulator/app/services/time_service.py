
from datetime import datetime

import pandas as pd

from app.core.config import (
    REFERENCE_TIMESTAMP,
    SAMPLING_INTERVAL_MINUTES,
)


def calculate_start_timestamp(
    last_timestamp: pd.Timestamp,
) -> pd.Timestamp:
    """
    Détermine le point de départ de la simulation.
    """

    reference_timestamp = pd.Timestamp(REFERENCE_TIMESTAMP)

    return max(last_timestamp, reference_timestamp)


def calculate_missing_timestamps(
    last_timestamp: pd.Timestamp,
    current_timestamp: datetime | pd.Timestamp | None = None,
) -> list[pd.Timestamp]:
    """
    Calcule les timestamps des mesures manquantes.

    Les nouvelles mesures commencent une minute après
    le timestamp de départ et s'arrêtent à l'heure actuelle.
    """

    if current_timestamp is None:
        current_timestamp = datetime.now()

    current_timestamp = pd.Timestamp(current_timestamp)
    last_timestamp = pd.Timestamp(last_timestamp)

    if current_timestamp.tz is not None or last_timestamp.tz is not None:
        raise ValueError(
            "Les timestamps doivent utiliser le même format sans fuseau horaire."
        )

    start_timestamp = calculate_start_timestamp(last_timestamp)

    # On conserve uniquement les minutes complètes.
    current_timestamp = current_timestamp.floor("min")

    first_missing_timestamp = (
        start_timestamp
        + pd.Timedelta(minutes=SAMPLING_INTERVAL_MINUTES)
    )

    if first_missing_timestamp > current_timestamp:
        return []

    timestamps = pd.date_range(
        start=first_missing_timestamp,
        end=current_timestamp,
        freq=f"{SAMPLING_INTERVAL_MINUTES}min",
    )

    return list(timestamps)


def get_simulation_plan(
    last_timestamp: pd.Timestamp,
    current_timestamp: datetime | pd.Timestamp | None = None,
) -> dict:
    """
    Retourne un résumé du calcul de simulation.
    """

    if current_timestamp is None:
        current_timestamp = datetime.now()

    current_timestamp = pd.Timestamp(current_timestamp)
    last_timestamp = pd.Timestamp(last_timestamp)

    start_timestamp = calculate_start_timestamp(last_timestamp)

    missing_timestamps = calculate_missing_timestamps(
        last_timestamp=last_timestamp,
        current_timestamp=current_timestamp,
    )

    return {
        "last_timestamp": str(last_timestamp),
        "reference_timestamp": REFERENCE_TIMESTAMP,
        "simulation_start": str(start_timestamp),
        "first_missing_timestamp": (
            str(missing_timestamps[0])
            if missing_timestamps else None
        ),
        "last_missing_timestamp": (
            str(missing_timestamps[-1])
            if missing_timestamps else None
        ),
        "missing_minutes": len(missing_timestamps),
        "current_timestamp": str(current_timestamp),
    }
