
from pathlib import Path
import shutil

import kagglehub
import pandas as pd


# Configuration Kaggle
DATASET_ID = "nphantawee/pump-sensor-data"
FILE_NAME = "sensor.csv"

# Destination dans le projet
OUTPUT_DIR = Path("datasets/raw/extracted")
OUTPUT_FILE = OUTPUT_DIR / FILE_NAME


def download_dataset() -> pd.DataFrame:

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Conserver le dataset existant
    if OUTPUT_FILE.exists() and OUTPUT_FILE.stat().st_size > 0:

        print("Dataset deja present localement.")
        print(f"Fichier conserve : {OUTPUT_FILE}")
        print(
            f"Taille : "
            f"{OUTPUT_FILE.stat().st_size / (1024 * 1024):.2f} MB"
        )

        print("\nChargement du dataset existant...")
        df = pd.read_csv(OUTPUT_FILE)

    else:

        print("Dataset absent. Telechargement depuis Kaggle...")

        dataset_path = Path(
            kagglehub.dataset_download(DATASET_ID)
        )

        print(f"\nDossier du dataset : {dataset_path}")

        # Rechercher le fichier CSV
        csv_files = [
            file
            for file in dataset_path.rglob("*")
            if file.is_file()
            and file.name.lower() == FILE_NAME.lower()
        ]

        if not csv_files:
            raise FileNotFoundError(
                f"{FILE_NAME} introuvable apres le telechargement. "
                f"Dossier inspecte : {dataset_path}"
            )

        source_file = csv_files[0]

        print(f"\nFichier trouve : {source_file}")

        if source_file.stat().st_size == 0:
            raise ValueError("Le fichier CSV telecharge est vide.")

        # Copier le fichier original
        shutil.copy2(source_file, OUTPUT_FILE)

        print(f"\nCopie sauvegardee : {OUTPUT_FILE}")

        # Charger les donnees
        df = pd.read_csv(OUTPUT_FILE)

    print("\nDataset charge avec succes.")
    print(f"Nombre de lignes : {len(df):,}")
    print(f"Nombre de colonnes : {len(df.columns)}")

    print("\nColonnes :")
    print(df.columns.tolist())

    print("\nApercu des 5 premieres lignes :")
    print(df.head())

    return df


if __name__ == "__main__":
    download_dataset()
