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


def _normalise_numeric(df: pd.DataFrame, numeric_columns: list[str]) -> pd.DataFrame:
    """
    Strip stray whitespace and coerce the given columns to numbers in place.

    e.g. a leading space (" 123") would make the raceId join match nothing, and a non-numeric position
    ("DNF") would break the winner comparison where position == 1. 
    
    Stripping then coercing turns the first into a real number and the second into NaN (null) so neither corrupts
    the output. 
    """
    for col in numeric_columns:
        # astype("string") first so .str.strip() works whether the column was
        # read as numbers or as object/strings; strip removes stray whitespace
        cleaned = df[col].astype("string").str.strip()
        df[col] = pd.to_numeric(cleaned, errors="coerce")
    return df


def _validate_lap_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fail if any non-null fastestLapTime is not in MM:SS.s format

    """
    col = config.FASTEST_LAP_COLUMN
    values = df[col].dropna().astype("string").str.strip()
    bad = values[~values.str.match(config.FASTEST_LAP_PATTERN)]
    if not bad.empty:
        sample = bad.unique()[:5].tolist()
        raise ValueError(
            f"{col} has {len(bad)} value(s) not in MM:SS.s format, e.g. {sample}. "
            f"Expected values like '01:29.4'."
        )
    return df

# Load races.csv and convert to DataFrame
# Called in main.py
# Takes filepath from `config.py` and returns the path along with column names
def load_races(path: Path = config.RACES_CSV) -> pd.DataFrame:
    df = _read_csv(path, config.RACES_COLUMNS)
    return _normalise_numeric(df, config.RACES_NUMERIC_COLUMNS)

# Load results.csv and convert to DataFrame
# Called in main.py
# Takes filepath from `config.py` and returns the path along with column names
def load_results(path: Path = config.RESULTS_CSV) -> pd.DataFrame:
    df = _read_csv(path, config.RESULTS_COLUMNS)
    df = _normalise_numeric(df, config.RESULTS_NUMERIC_COLUMNS)
    return _validate_lap_format(df)
