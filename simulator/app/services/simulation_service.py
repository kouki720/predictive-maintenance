
from __future__ import annotations

import threading
from datetime import datetime

import numpy as np
import pandas as pd

from app.core.config import (
    DATASET_FILE,
    STATUS_COLUMN,
    TIMESTAMP_COLUMN,
)
from app.services.dataset_service import (
    load_dataset,
    get_latest_timestamp,
)
from app.services.time_service import (
    calculate_missing_timestamps,
    get_simulation_plan,
)


_simulation_lock = threading.Lock()

NORMAL_STATUS = "NORMAL"


def get_sensor_columns(df: pd.DataFrame) -> list[str]:
    """Retourne les colonnes des 20 capteurs."""

    return [
        column
        for column in df.columns
        if column not in {TIMESTAMP_COLUMN, STATUS_COLUMN}
    ]


def prepare_historical_data(
    df: pd.DataFrame,
    sensor_columns: list[str],
) -> tuple[np.ndarray, np.ndarray]:
    """
    Prépare les transitions historiques NORMAL.

    Une transition est conservée uniquement si :
    - les deux lignes sont NORMAL ;
    - les 20 capteurs ont des valeurs disponibles ;
    - les timestamps sont espacés d'une minute.
    """

    df = df.sort_values(TIMESTAMP_COLUMN).reset_index(drop=True)

    values = df[sensor_columns].to_numpy(dtype=float)

    normal_mask = (
        df[STATUS_COLUMN]
        .astype(str)
        .eq(NORMAL_STATUS)
        .to_numpy()
    )

    valid_rows = np.isfinite(values).all(axis=1)

    consecutive_minutes = (
        df[TIMESTAMP_COLUMN]
        .diff()
        .eq(pd.Timedelta(minutes=1))
        .to_numpy()
    )

    valid_pairs = (
        normal_mask[:-1]
        & normal_mask[1:]
        & valid_rows[:-1]
        & valid_rows[1:]
        & consecutive_minutes[1:]
    )

    previous_values = values[:-1][valid_pairs]
    next_values = values[1:][valid_pairs]

    if len(previous_values) == 0:
        raise ValueError(
            "Aucune transition historique NORMAL complète disponible."
        )

    historical_deltas = next_values - previous_values

    normal_values = values[
        normal_mask & valid_rows
    ]

    if len(normal_values) == 0:
        raise ValueError(
            "Aucune mesure NORMAL complète disponible."
        )

    sensor_medians = np.median(
        normal_values,
        axis=0,
    )

    return historical_deltas, sensor_medians



def get_initial_values(
    df: pd.DataFrame,
    sensor_columns: list[str],
    sensor_medians: np.ndarray,
) -> np.ndarray:
    """Récupère la dernière valeur connue de chaque capteur."""

    last_values = (
        df.sort_values(TIMESTAMP_COLUMN)[sensor_columns]
        .ffill()
        .iloc[-1]
        .to_numpy(dtype=float)
        .copy()  # Important : tableau modifiable
    )

    missing_mask = ~np.isfinite(last_values)

    last_values[missing_mask] = sensor_medians[missing_mask]

    return last_values


def generate_measurements(
    df: pd.DataFrame,
    timestamps: list[pd.Timestamp],
) -> pd.DataFrame:
    """Génère les nouvelles mesures avec le statut NORMAL."""

    sensor_columns = get_sensor_columns(df)

    historical_deltas, sensor_medians = prepare_historical_data(
        df,
        sensor_columns,
    )

    current_values = get_initial_values(
        df,
        sensor_columns,
        sensor_medians,
    )

    rng = np.random.default_rng()

    generated_rows = []

    for timestamp in timestamps:

        # Sélection d'une variation historique complète.
        selected_index = rng.integers(
            0,
            len(historical_deltas),
        )

        delta = historical_deltas[selected_index]

        # Application de la variation historique.
        next_values = current_values + delta

        # Petite correction pour éviter une dérive excessive.
        next_values += 0.002 * (
            sensor_medians - current_values
        )

        current_values = next_values

        row = {
            TIMESTAMP_COLUMN: timestamp,
        }

        for index, sensor in enumerate(sensor_columns):
            row[sensor] = float(current_values[index])

        row[STATUS_COLUMN] = NORMAL_STATUS

        generated_rows.append(row)

    return pd.DataFrame(
        generated_rows,
        columns=df.columns,
    )


def run_simulation(
    current_timestamp: datetime | pd.Timestamp | None = None,
) -> dict:
    """
    Lance la simulation et ajoute les mesures au CSV.

    Le point de départ est déterminé par time_service.py :
    max(dernier timestamp, REFERENCE_TIMESTAMP).
    """

    with _simulation_lock:

        # 1. Charger le dataset existant.
        df = load_dataset()

        last_timestamp = get_latest_timestamp(df)

        # 2. Construire le plan de simulation.
        plan = get_simulation_plan(
            last_timestamp=last_timestamp,
            current_timestamp=current_timestamp,
        )

        # 3. Calculer les timestamps manquants.
        timestamps = calculate_missing_timestamps(
            last_timestamp=last_timestamp,
            current_timestamp=current_timestamp,
        )

        if not timestamps:
            return {
                "status": "success",
                "message": "Aucune nouvelle mesure à générer.",
                "generated_count": 0,
                "simulation_plan": plan,
                "new_measurements": [],
            }

        # 4. Générer les nouvelles mesures.
        new_df = generate_measurements(
            df=df,
            timestamps=timestamps,
        )

        # 5. Contrôles avant écriture.
        sensor_columns = get_sensor_columns(df)

        if new_df[sensor_columns].isna().any().any():
            raise ValueError(
                "Les nouvelles mesures contiennent des valeurs manquantes."
            )

        if not np.isfinite(
            new_df[sensor_columns].to_numpy(dtype=float)
        ).all():
            raise ValueError(
                "Les nouvelles mesures contiennent des valeurs infinies."
            )

        if not new_df[STATUS_COLUMN].eq(NORMAL_STATUS).all():
            raise ValueError(
                "Toutes les nouvelles mesures doivent être NORMAL."
            )

        if not new_df[TIMESTAMP_COLUMN].is_monotonic_increasing:
            raise ValueError(
                "Les timestamps générés ne sont pas chronologiques."
            )

        # 6. Écriture dans le même CSV.
        new_df.to_csv(
            DATASET_FILE,
            mode="a",
            header=False,
            index=False,
            encoding="utf-8",
            date_format="%Y-%m-%d %H:%M:%S",
        )

        # 7. Préparer les données de réponse.
        response_df = new_df.copy()

        response_df[TIMESTAMP_COLUMN] = (
            response_df[TIMESTAMP_COLUMN].astype(str)
        )

        return {
            "status": "success",
            "message": "Simulation completed successfully.",
            "generated_count": len(response_df),
            "machine_status": NORMAL_STATUS,
            "simulation_plan": plan,
            "first_generated_timestamp": str(
                response_df[TIMESTAMP_COLUMN].iloc[0]
            ),
            "last_generated_timestamp": str(
                response_df[TIMESTAMP_COLUMN].iloc[-1]
            ),
            "new_measurements": response_df.to_dict(
                orient="records"
            ),
        }
