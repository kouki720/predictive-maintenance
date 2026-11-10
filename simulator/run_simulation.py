
import json
import shutil
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SELECTED_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "extracted"
    / "sensor_selected.csv"
)

SIMULATION_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "extracted"
    / "sensor_simulation.csv"
)

API_URL = "http://127.0.0.1:8000"


def prepare_dataset():

    if not SELECTED_FILE.exists():
        raise FileNotFoundError(
            f"Dataset source introuvable : {SELECTED_FILE}"
        )

    # Initialisation uniquement lors de la première exécution.
    # Ne jamais écraser les données déjà simulées.
    if not SIMULATION_FILE.exists():
        shutil.copy2(SELECTED_FILE, SIMULATION_FILE)

        print("Dataset de simulation initialisé.")

    else:
        print("Dataset de simulation existant conservé.")


def call_simulation_api():

    health_url = f"{API_URL}/health"

    with urllib.request.urlopen(
        health_url,
        timeout=30
    ) as response:

        health = json.load(response)

    if health.get("status", "").lower() not in ("ok", "healthy"):
        raise RuntimeError("FastAPI simulator is not healthy.")

    request = urllib.request.Request(
        f"{API_URL}/api/simulation/run",
        data=b"",
        method="POST",
        headers={"Accept": "application/json"},
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:

        result = json.load(response)

    if result.get("status") != "success":
        raise RuntimeError(
            f"Simulation failed: {result}"
        )

    print("FastAPI simulation completed successfully.")


def main():

    print("=" * 60)
    print("FASTAPI SENSOR SIMULATION")
    print("=" * 60)

    prepare_dataset()

    call_simulation_api()


if __name__ == "__main__":
    main()
