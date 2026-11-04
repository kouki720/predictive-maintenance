
from pathlib import Path

import pandas as pd

from app.core.config import (
    DATASET_FILE,
    EXPECTED_SENSOR_COUNT,
    STATUS_COLUMN,
    TIMESTAMP_COLUMN,
)


def load_dataset() -> pd.DataFrame:
    """
    Charge le dataset temporel et vérifie sa structure.
    Aucune modification n'est appliquée au fichier source.
    """

    dataset_path = Path(DATASET_FILE)

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset introuvable : {dataset_path}"
        )

    if dataset_path.stat().st_size == 0:
        raise ValueError("Le fichier dataset est vide.")

    df = pd.read_csv(dataset_path)

    # Vérification des colonnes obligatoires
    required_columns = {
        TIMESTAMP_COLUMN,
        STATUS_COLUMN,
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Colonnes obligatoires manquantes : {missing_columns}"
        )

    # Vérification du nombre de capteurs
    sensor_columns = [
        column
        for column in df.columns
        if column not in {TIMESTAMP_COLUMN, STATUS_COLUMN}
    ]

    if len(sensor_columns) != EXPECTED_SENSOR_COUNT:
        raise ValueError(
            f"Nombre de capteurs incorrect : "
            f"{len(sensor_columns)} au lieu de "
            f"{EXPECTED_SENSOR_COUNT}."
        )

    # Conversion des timestamps
    df[TIMESTAMP_COLUMN] = pd.to_datetime(
        df[TIMESTAMP_COLUMN],
        errors="coerce",
    )

    if df[TIMESTAMP_COLUMN].isna().any():
        raise ValueError(
            "Le dataset contient des timestamps invalides."
        )

    if df.empty:
        raise ValueError("Le dataset ne contient aucune mesure.")

    return df


def get_latest_timestamp(df: pd.DataFrame) -> pd.Timestamp:


    if df.empty:
        raise ValueError("Impossible de récupérer la date : dataset vide.")

    return df[TIMESTAMP_COLUMN].max()


def get_dataset_summary(df: pd.DataFrame) -> dict:


    sensor_columns = [
        column
        for column in df.columns
        if column not in {TIMESTAMP_COLUMN, STATUS_COLUMN}
    ]

    return {
        "file": str(DATASET_FILE),
        "rows": len(df),
        "columns": len(df.columns),
        "sensor_count": len(sensor_columns),
        "first_timestamp": str(df[TIMESTAMP_COLUMN].min()),
        "last_timestamp": str(get_latest_timestamp(df)),
    }
