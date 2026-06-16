"""
Extract step: read the source CSV files into DataFrames.

"""

from pathlib import Path
import pandas as pd
from . import config

# reusable CSV read function
def _read_csv(path: Path, expected_columns: list[str]) -> pd.DataFrame:
    """
    This function (_read_csv) is called by load_races and load_results
    
    Parameters path and expected columns are passed to this function
    once extracted by the load_races and load_results functions

    """
    # handle missing filepath with explicit error message
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")

    # read CSV into DataFrame and handle a corrupt file (e.g. partial
    # write or failed job). Rather than EmptyDataError surface it as an explicit ValueError
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"{path.name} is empty: no columns to parse") from exc
    # expected columns derived from the list of strings in config
    missing = [col for col in expected_columns if col not in df.columns]
    # path.name provides the csv path (e.g. races.csv) and prints which columns are absent for debugging
    if missing:
        raise ValueError(f"{path.name} is missing expected columns: {missing}")
    # function returns the DataFrame
    return df

# Load races.csv and convert to DataFrame
# Called in main.py
# Takes filepath from `config.py` and returns the path along with column names
def load_races(path: Path = config.RACES_CSV) -> pd.DataFrame:
    return _read_csv(path, config.RACES_COLUMNS)

# Load results.csv and convert to DataFrame
# Called in main.py
# Takes filepath from `config.py` and returns the path along with column names
def load_results(path: Path = config.RESULTS_CSV) -> pd.DataFrame:
    return _read_csv(path, config.RESULTS_COLUMNS)
