
from pathlib import Path

import pandas as pd


# =====================================================
# CONFIGURATION
# =====================================================

INPUT_FILE = Path("datasets/raw/extracted/sensor.csv")

OUTPUT_DIR = Path("datasets/raw/extracted")
OUTPUT_FILE = OUTPUT_DIR / "sensor_selected.csv"

ORIGINAL_START_YEAR = 2018
TARGET_START_YEAR = 2026


# =====================================================
# SENSOR MAPPING
# =====================================================

SENSOR_MAPPING = {
    "sensor_00": "motor_casing_vibration",
    "sensor_04": "motor_speed",
    "sensor_05": "motor_current",
    "sensor_06": "motor_active_power",
    "sensor_13": "motor_coupling_vibration",
    "sensor_18": "pump_casing_vibration",
    "sensor_37": "pump_lube_oil_reservoir_level",
    "sensor_38": "pump_lube_oil_return_temperature",
    "sensor_39": "pump_lube_oil_supply_temperature",
    "sensor_40": "pump_thrust_bearing_active_temperature",
    "sensor_41": "motor_non_drive_end_bearing_temperature_1",
    "sensor_42": "motor_non_drive_end_bearing_temperature_2",
    "sensor_43": "pump_thrust_bearing_inactive_temperature",
    "sensor_44": "pump_drive_end_bearing_temperature_1",
    "sensor_45": "pump_non_drive_end_bearing_temperature_1",
    "sensor_47": "pump_drive_end_bearing_temperature_2",
    "sensor_34": "pump_inlet_flow",
    "sensor_35": "pump_discharge_flow",
    "sensor_48": "pump_inlet_pressure",
    "sensor_51": "pump_discharge_pressure_2",
}


# =====================================================
# SENSOR SELECTION + DATE SHIFT
# =====================================================

def select_sensors():

    print("=" * 60)
    print("SENSOR SELECTION AND COLUMN MAPPING")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Source dataset not found: {INPUT_FILE}"
        )

    # 1. Load original dataset
    df = pd.read_csv(INPUT_FILE)

    print(f"\nOriginal dimensions: {df.shape}")

    # 2. Verify required columns
    required_columns = [
        "timestamp",
        "machine_status",
        *SENSOR_MAPPING.keys()
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # 3. Select columns
    selected_columns = [
        "timestamp",
        *SENSOR_MAPPING.keys(),
        "machine_status"
    ]

    selected_df = df[selected_columns].copy()

    # 4. Convert timestamp
    selected_df["timestamp"] = pd.to_datetime(
        selected_df["timestamp"],
        errors="raise"
    )

    # 5. Shift dates from 2018 to 2026
    if not (selected_df["timestamp"].dt.year == ORIGINAL_START_YEAR).all():
        raise ValueError(
            f"Expected all timestamps to belong to {ORIGINAL_START_YEAR}."
        )

    year_difference = TARGET_START_YEAR - ORIGINAL_START_YEAR

    selected_df["timestamp"] = (
        selected_df["timestamp"]
        + pd.DateOffset(years=year_difference)
    )

    # 6. Rename sensor columns
    selected_df.rename(
        columns=SENSOR_MAPPING,
        inplace=True
    )

    # 7. Create output directory
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 8. Save selected dataset
    selected_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
        date_format="%Y-%m-%d %H:%M:%S"
    )

    # 9. Display results
    print("\nSelected sensors:")
    for original, new_name in SENSOR_MAPPING.items():
        print(f"{original} -> {new_name}")

    print("\nDate transformation:")
    print(f"Original start: {df['timestamp'].iloc[0]}")
    print(f"New start:      {selected_df['timestamp'].iloc[0]}")
    print(f"New end:        {selected_df['timestamp'].iloc[-1]}")

    print("\nFinal dataset information:")
    print(f"Rows: {len(selected_df):,}")
    print(f"Columns: {len(selected_df.columns)}")
    print(f"Selected sensors: {len(SENSOR_MAPPING)}")

    print(f"\nOutput saved to: {OUTPUT_FILE}")

    print("\n" + "=" * 60)
    print("SENSOR SELECTION COMPLETED")
    print("=" * 60)

    return selected_df


if __name__ == "__main__":
    select_sensors()
