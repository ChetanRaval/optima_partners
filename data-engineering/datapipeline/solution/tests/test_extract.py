"""
Test Extract step at pipeline.extract.py

1. Test file exists + all columns exist + valid DataFrame against load_races()
2. Test missing file against load_races() and check for FileNotFoundError 
3. Test missing column against load_results() and check for ValueError
4. Test corrupt/zero byte file as a result of a failed upstream job

"""

import pandas as pd
import pytest
from pipeline import extract


def test_load_races_reads_expected_columns(tmp_path):
    """
    Create a one row DataFrame with load_races() expected columns and write to temp CSV
    Calls the load_races() function and ensures that the returned columns match the list
    defined in config.py.

    """

    # create temp csv
    csv = tmp_path / "races.csv"
    # create DataFrame and write to temp csv
    pd.DataFrame(
        {
            "raceId": [1],
            "year": [2024],
            "round": [1],
            "name": ["Bahrain Grand Prix"],
            "date": ["2024-03-02"],
            "time": ["15:00:00"],
        }
    ).to_csv(csv, index=False)

    # call function in extract.py
    df = extract.load_races(csv)
    # ensure the list of columns matches those in the config file
    assert list(df.columns) == extract.config.RACES_COLUMNS
    # ensure the dataframe has not been altered after function call
    assert len(df) == 1


def test_load_missing_file_raises(tmp_path):
    """
    Call load_races() function with a non-existent path 
    to ensure FileNotFound error is raised.

    """
    with pytest.raises(FileNotFoundError):
        extract.load_races(tmp_path / "does_not_exist.csv")


def test_load_missing_columns_raises(tmp_path):
    """
    Create DataFrame with missing columns and ensure ValueError is raised
    along with explicit message. 

    """
    
    # create temp csv
    csv = tmp_path / "results.csv"
    # create DataFrame with missing columns and write to temp csv
    pd.DataFrame({"resultId": [1], "raceId": [1]}).to_csv(csv, index=False)
    # ensure that test raises ValueError with substring
    with pytest.raises(ValueError, match="missing expected columns"):
        extract.load_results(csv)


def test_empty_file_raises_friendly_error(tmp_path):
    """
    Test an empty file (partial write, failed upstream job) should fail
    with the module's own explicit error, not pandas raw output EmptyDataError

    """

    # create temp csv
    csv = tmp_path / "races.csv"
    # create the csv but with no content/zero-bytes
    csv.touch()
    # call the load_races() function on the empty CSV and check for ValueError
    # `match = "empty"` regex for existence of this substring in exception string
    # test fails on no exception or different exception
    with pytest.raises(ValueError, match="empty"):
        extract.load_races(csv)
