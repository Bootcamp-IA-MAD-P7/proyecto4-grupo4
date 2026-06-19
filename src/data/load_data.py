import os
import pandas as pd
import kagglehub


RAW_CSV_NAME = "unicorns till sep 2022.csv"
KAGGLE_DATASET = "ramjasmaurya/unicorn-startups"


def download_dataset() -> str:
    """Download dataset from Kaggle and return the path to the CSV file."""
    path = kagglehub.dataset_download(KAGGLE_DATASET)
    csv_path = os.path.join(path, RAW_CSV_NAME)
    return csv_path


def load_raw(csv_path: str = None) -> pd.DataFrame:
    """Load the raw dataset. Downloads from Kaggle if no path is provided."""
    if csv_path is None:
        csv_path = download_dataset()
    return pd.read_csv(csv_path)


def save_raw(df: pd.DataFrame, output_dir: str = "data/raw") -> str:
    """Save raw dataframe to data/raw/."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "dataset_raw.csv")
    df.to_csv(path, index=False)
    return path
