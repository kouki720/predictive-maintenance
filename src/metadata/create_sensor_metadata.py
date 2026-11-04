
from pathlib import Path
import json
import pandas as pd


# =====================================================
# CONFIGURATION
# =====================================================

INPUT_FILE = Path(
    "datasets/raw/extracted/sensor_selected.csv"
)

OUTPUT_DIR = Path("datasets/metadata")

OUTPUT_FILE = OUTPUT_DIR / "sensor_metadata.json"


# =====================================================
# DATASET INFORMATION
# =====================================================

DATASET_METADATA = {
    "dataset_name": "Pump Sensor Data",
    "source": "Kaggle",
    "source_dataset": "nphantawee/pump-sensor-data",

    "original_file": "sensor.csv",

    "selected_file": "sensor_selected.csv",

    "temporal_file": "sensor_temporal.csv",

    "original_period": {
        "start": "2018-04-01 00:00:00",
        "end": "2018-08-31 23:59:00"
    },

    "current_period": {
        "start": "2026-04-01 00:00:00",
        "end": "2026-08-31 23:59:00"
    },

    "date_transformation": {
        "applied": True,
        "original_year": 2018,
        "target_year": 2026,
        "type": "artificial_date_shift",
        "description": (
            "Timestamps were artificially shifted "
            "from 2018 to 2026. Measurements remain "
            "from the original dataset."
        )
    },

    "sampling_frequency": "1 minute",

    "total_rows": 220320,

    "total_selected_sensors": 20,

    "status_column": "machine_status"
}


# =====================================================
# SENSOR DEFINITIONS
# =====================================================

SENSOR_METADATA = {

    "sensor_00": {
        "sensor_name": "motor_casing_vibration",
        "sensor_type": "vibration",
        "unit": None,
        "description": "Measures vibration of the motor casing."
    },

    "sensor_04": {
        "sensor_name": "motor_speed",
        "sensor_type": "speed",
        "unit": None,
        "description": "Measures motor rotational speed."
    },

    "sensor_05": {
        "sensor_name": "motor_current",
        "sensor_type": "electrical_current",
        "unit": None,
        "description": "Measures electrical current of the motor."
    },

    "sensor_06": {
        "sensor_name": "motor_active_power",
        "sensor_type": "power",
        "unit": None,
        "description": "Measures active power of the motor."
    },

    "sensor_13": {
        "sensor_name": "motor_coupling_vibration",
        "sensor_type": "vibration",
        "unit": None,
        "description": "Measures vibration around the motor coupling."
    },

    "sensor_18": {
        "sensor_name": "pump_casing_vibration",
        "sensor_type": "vibration",
        "unit": None,
        "description": "Measures vibration of the pump casing."
    },

    "sensor_37": {
        "sensor_name": "pump_lube_oil_reservoir_level",
        "sensor_type": "level",
        "unit": None,
        "description": "Measures the pump lubrication oil reservoir level."
    },

    "sensor_38": {
        "sensor_name": "pump_lube_oil_return_temperature",
        "sensor_type": "temperature",
        "unit": None,
        "description": "Measures lubrication oil return temperature."
    },

    "sensor_39": {
        "sensor_name": "pump_lube_oil_supply_temperature",
        "sensor_type": "temperature",
        "unit": None,
        "description": "Measures lubrication oil supply temperature."
    },

    "sensor_40": {
        "sensor_name": "pump_thrust_bearing_active_temperature",
        "sensor_type": "temperature",
        "unit": None,
        "description": "Measures active thrust bearing temperature."
    },

    "sensor_41": {
        "sensor_name": "motor_non_drive_end_bearing_temperature_1",
        "sensor_type": "temperature",
        "unit": None,
        "description": "Measures motor non-drive-end bearing temperature."
    },

    "sensor_42": {
        "sensor_name": "motor_non_drive_end_bearing_temperature_2",
        "sensor_type": "temperature",
        "unit": None,
        "description": "Measures another motor non-drive-end bearing temperature."
    },

    "sensor_43": {
        "sensor_name": "pump_thrust_bearing_inactive_temperature",
        "sensor_type": "temperature",
        "unit": None,
        "description": "Measures inactive thrust bearing temperature."
    },

    "sensor_44": {
        "sensor_name": "pump_drive_end_bearing_temperature_1",
        "sensor_type": "temperature",
        "unit": None,
        "description": "Measures pump drive-end bearing temperature."
    },

    "sensor_45": {
        "sensor_name": "pump_non_drive_end_bearing_temperature_1",
        "sensor_type": "temperature",
        "unit": None,
        "description": "Measures pump non-drive-end bearing temperature."
    },

    "sensor_47": {
        "sensor_name": "pump_drive_end_bearing_temperature_2",
        "sensor_type": "temperature",
        "unit": None,
        "description": "Measures another pump drive-end bearing temperature."
    },

    "sensor_34": {
        "sensor_name": "pump_inlet_flow",
        "sensor_type": "flow",
        "unit": None,
        "description": "Measures fluid flow at the pump inlet."
    },

    "sensor_35": {
        "sensor_name": "pump_discharge_flow",
        "sensor_type": "flow",
        "unit": None,
        "description": "Measures fluid flow at the pump discharge."
    },

    "sensor_48": {
        "sensor_name": "pump_inlet_pressure",
        "sensor_type": "pressure",
        "unit": None,
        "description": "Measures pressure at the pump inlet."
    },

    "sensor_51": {
        "sensor_name": "pump_discharge_pressure_2",
        "sensor_type": "pressure",
        "unit": None,
        "description": "Measures pump discharge pressure."
    }
}


# =====================================================
# METADATA GENERATION
# =====================================================

def create_sensor_metadata():

    print("=" * 60)
    print("SENSOR METADATA MANAGEMENT")
    print("=" * 60)

    # 1. Check input file
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    # 2. Read dataset columns
    df = pd.read_csv(INPUT_FILE, nrows=0)

    dataset_columns = set(df.columns)

    # 3. Generate sensor metadata
    sensors = []

    for sensor_id, metadata in SENSOR_METADATA.items():

        sensor_name = metadata["sensor_name"]

        if sensor_name not in dataset_columns:
            raise ValueError(
                f"Sensor column not found: {sensor_name}"
            )

        sensors.append({

            "sensor_id": sensor_id,

            "source_column": sensor_id,

            "selected_column": sensor_name,

            "sensor_name": sensor_name,

            "sensor_type": metadata["sensor_type"],

            "unit": metadata["unit"],

            "machine_id": None,

            "description": metadata["description"],

            "availability": True,

            "metadata_status": "provisional"

        })

    # 4. Verify metadata
    if len(sensors) != 20:
        raise ValueError(
            f"Expected 20 sensors, found {len(sensors)}"
        )

    sensor_ids = [
        sensor["sensor_id"] for sensor in sensors
    ]

    if len(sensor_ids) != len(set(sensor_ids)):
        raise ValueError("Duplicate sensor IDs detected.")

    # 5. Build final JSON structure
    final_metadata = {
        "dataset": DATASET_METADATA,
        "sensors": sensors
    }

    # 6. Create output directory
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # 7. Save JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:

        json.dump(
            final_metadata,
            file,
            indent=4,
            ensure_ascii=False
        )

    # 8. Display results
    print("\nDataset metadata created.")

    print(f"Total sensors: {len(sensors)}")

    print("\nSensors by type:")

    for sensor_type, count in (
        pd.Series(
            [sensor["sensor_type"] for sensor in sensors]
        ).value_counts().items()
    ):
        print(f"{sensor_type}: {count}")

    print(f"\nJSON saved to: {OUTPUT_FILE}")

    print("\n" + "=" * 60)
    print("SENSOR METADATA MANAGEMENT COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    create_sensor_metadata()
