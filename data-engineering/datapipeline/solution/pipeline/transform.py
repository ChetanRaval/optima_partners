"""
Transform step: join races with winners and build the per-year stats records.
Inputs from extract.py and outputs into load.write_stats

Creates a registry of metrics that can be expanded in a self-contained way, so that contributors can add new output fields without touching the rest of the code.

"""

from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd
from . import config

def build_winners(results: pd.DataFrame) -> pd.DataFrame:
    """
    Return one row per race for the winning driver (finished in position 1).

    Keeps the winner's driverId and fastestLapTime rather than overall lap time per race.
    This assumption has been noted in the README
    """
    # assign and return the winner where position = 1 (determined by config file)
    winners = results[results["position"] == config.WINNING_POSITION]
    # return the winner's raceId, driverId, and fastestLapTime
    # reset_index renumbers rows starting from 0 - discard original row indices
    return winners[["raceId", "driverId", "fastestLapTime"]].reset_index(drop=True)


def build_race_datetime(date: str, time) -> str:
    """
    Combine a race date and time into a datetime string with milliseconds.
    All times in UTC and remain that way. 
    When the time is missing, defaults to 00:00:00.
    """
    # if the time is missing or blank, default to time declared in config.py
    if pd.isna(time) or str(time).strip() == "":
        time = config.DEFAULT_TIME
    # concatenate date and time columns to create a datetime object.
    # utc=True localises to UTC so the UTC assumption is enforced rather than implicit from source data
    dt = pd.to_datetime(f"{date} {time}", utc=True)
    # use format defined in config.py to adhere to datetime requirements
    return dt.strftime(config.DATETIME_FORMAT)


@dataclass(frozen=True)
class Metric:
    """
    One output field: its display name (from config) and a pure function that
    derives its value from a single merged race row.

    Each metric is self-contained: adding a new output field means appending one
    Metric to the METRICS registry below, without touching the others or the
    record builder function. The function owns that field's logic, including any null
    handling, so contributors do not need to understand the rest of the output.
    """
    name: str
    fn: Callable[[pd.Series], Any]


# Registry of output fields, in output order. This is the single source of
# truth for the shape of each record - add a metric by appending one entry.
# Races with no winner have a NaN driverId (left join), so winner-derived fields
# return None (maps to null in JSON) when the driverId is missing.
METRICS = [
    Metric(config.RACE_NAME, lambda r: r["name"]),
    # explicitly cast round to int (maps to a number in JSON)
    Metric(config.RACE_ROUND, lambda r: int(r["round"])),
    # reuse the datetime builder so the format/UTC logic lives in one place
    Metric(config.RACE_DATETIME, lambda r: build_race_datetime(r["date"], r["time"])),
    # cast to int when present, else None for result-less races
    Metric(config.RACE_WINNING_DRIVER_ID,
           lambda r: int(r["driverId"]) if pd.notna(r["driverId"]) else None),
    Metric(config.RACE_FASTEST_LAP,
           lambda r: r["fastestLapTime"] if pd.notna(r["driverId"]) else None),
]


def _to_record(row: pd.Series) -> dict:
    """
    Build one output dictionary by applying every metric from the registry.

    """
    return {metric.name: metric.fn(row) for metric in METRICS}


# Called in main.py
def build_stats_by_year(races: pd.DataFrame, results: pd.DataFrame) -> dict[int, list[dict]]:
    """
    Join races with their winners and group records by year, sorted by round.

    Races with no results are kept with a null winner and fastest lap.
    This decision has been documented in README

    Parameters to this function are sourced from:
    - extract.load_races(): one row per race
    - extract.load_results: one row per driver per race

    Returns keys as ints/numbers and values are a list of race-record dictionaries.

    """
    
    # Reduces results to one winner row per race
    winners = build_winners(results)
    # Left join races dataframe onto winners dataframe so that every race is kept even if it has no matching winner (handled with null)
    merged = races.merge(winners, on="raceId", how="left")

    # define empty dictionary and make sure keys are ints and values are lists of dicts
    stats: dict[int, list[dict]] = {}
    # Group the merged rows by year, return key (year) and that year's races
    for year, group in merged.groupby("year"):
        # within each year, sort races by round (chronological order in a season)
        ordered = group.sort_values("round")
        # convert each row to a record using the helper function
        # `_` discards the index since we only need the row
        records = [_to_record(row) for _, row in ordered.iterrows()]
        # store the list under the year key, cast as an int/number
        stats[int(year)] = records
    # hand the dictionary to main.py which then passes it to load.write_stats()
    return stats
