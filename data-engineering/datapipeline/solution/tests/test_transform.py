"""
Test Transform step at pipeline.transform.py

1. Create helper functions that generate test dataframes for races and results
2. Test that build_winners() only retains P1 drivers, handles missing results, and fastestLapTime is the winner's, not overall
3. Test build_race_datetime() outputs correct format and handles missing times
4. Integration test (build_stats_by_year()) to ensure stats are sorted by the race round for ordering and data type adherence
5. Integration test (build_stats_by_year()) to ensure race with no results returns None/nulls and fallback datetime value is present
6. Test to ensure that every race appears once in the output and none are dropped or duplicated 
7. Ensure that the metrics registry drives the output fields and order, so that adding a metric to the registry is the only way to add an output field
8. Integration test (build_stats_by_year()) to check final shape of data validated against requirements


"""

import numpy as np
import pandas as pd

from pipeline import config, transform

def _races():
    """
    Helper function to create a races DataFrame
   - Rounds are out of order to test sorting
   - Race 12 has no matching result (race with no winner test)
   - Race 12 time is NaN (race with missing time test)

    """
    return pd.DataFrame(
        {
            "raceId": [10, 11, 12],
            "year": [2024, 2024, 2024],
            "round": [2, 1, 3],
            "name": ["B GP", "A GP", "C GP (no results)"],
            "date": ["2024-04-07", "2024-03-02", "2024-04-21"],
            "time": ["14:00:00", "15:00:00", np.nan],  # round 3 has a missing time
        }
    )

def _results():
    """
    Helper function to create a results DataFrame
    - 2 results per race for raceId 10 and 11
    - P1 and P2 in each
    - No result for raceId = 12

    """
    return pd.DataFrame(
        {
            "resultId": [1, 2, 3, 4],
            "raceId": [10, 10, 11, 11],
            "driverId": [44, 1, 1, 44],
            "position": [1, 2, 1, 2],
            "fastestLapTime": ["01:29.4", "01:29.0", "01:30.1", "01:30.5"],
        }
    )


def test_build_winners_keeps_position_one_only():
    """
    Test asserts that build_winners() function in transform.py keeps P1 drivers
    and only keeps raceId, driverId, and fastestLapTime

    Race 12 absent from results so it never appears in the winners table. 
    The NaN/None handling is in test_result_less_race_has_null_winner_and_lap

    Ensures that the retained fastestLapTime is the winner's lap, not the fastest overall lap

    """
    winners = transform.build_winners(_results())
    assert set(winners["raceId"]) == {10, 11}
    assert winners.loc[winners["raceId"] == 10, "driverId"].item() == 44
    assert winners.loc[winners["raceId"] == 10, "fastestLapTime"].item() == "01:29.4"


def test_build_race_datetime_formats_with_milliseconds():
    """
    Ensures build_race_datetime() outputs correct/expected format

    """
    assert transform.build_race_datetime("2024-07-07", "14:00:00") == "2024-07-07T14:00:00.000"


def test_build_race_datetime_defaults_missing_time_to_midnight():
    """
    Ensures build_race_datetime() defaults missing/NaN times to 00:00:00 as per objective instructions

    """
    assert transform.build_race_datetime("2024-07-07", np.nan) == "2024-07-07T00:00:00.000"
    assert transform.build_race_datetime("2024-07-07", "") == "2024-07-07T00:00:00.000"

# Integration Test
def test_build_stats_sorts_by_round_and_types_are_numeric():
    """
    Runs full pipeline and ensures that stats are sorted by the race round
    for chronological ordering using the helper function dataframes.

    Also asserts that data types are adhered to (round and driverId are ints)
    """

    stats = transform.build_stats_by_year(_races(), _results())
    records = stats[2024]

    assert [r[config.RACE_ROUND] for r in records] == [1, 2, 3]
    first = records[0]
    assert isinstance(first[config.RACE_ROUND], int)
    assert isinstance(first[config.RACE_WINNING_DRIVER_ID], int)


# Integration Test
def test_result_less_race_has_null_winner_and_lap():
    """
    Test that a race with no results yields None/nulls to ensure we are not suppressing race data.

    Gets race without results from helper dataframes, passes to build_stats_by_year()
    and asserts that None values are returned with fallback datetime value.

    """
    stats = transform.build_stats_by_year(_races(), _results())
    no_results = next(r for r in stats[2024] if r[config.RACE_NAME] == "C GP (no results)")
    assert no_results[config.RACE_WINNING_DRIVER_ID] is None
    assert no_results[config.RACE_FASTEST_LAP] is None
    assert no_results[config.RACE_DATETIME] == "2024-04-21T00:00:00.000"

# Integration Test
def test_every_source_race_appears_exactly_once():
    """
    Reconcile output against source: every race in the source races DataFrame
    should appear exactly once across the output, with none dropped or duplicated.

    Flattens all per-year records and compares race names (unique per race in
    the source) against the source, asserting equal counts and a one-to-one match.

    """
    races = _races()
    stats = transform.build_stats_by_year(races, _results())

    # flatten every year's records into a single list
    output_names = [r[config.RACE_NAME] for records in stats.values() for r in records]

    # same number of output records as source races (nothing dropped or duplicated)
    assert len(output_names) == len(races)
    # every source race appears exactly once in the output
    assert sorted(output_names) == sorted(races["name"])


def test_registry_drives_output_fields():
    """
    The output keys are exactly the registry's metric names, in registry order.

    The METRICS registry is the single source of truth for
    the output shape, so adding a metric to this is the only way to add an output field
    (and a contributor cannot add one without it appearing in the output).
    """
    # generate the record and loop over the keys to ensure that all metrics exist in the output and in the same order as the registry
    record = transform.build_stats_by_year(_races(), _results())[2024][0]
    assert list(record.keys()) == [m.name for m in transform.METRICS]


# Integration Test
def test_matches_assignment_example_shape():
    """
    Asserts final shape of data validated against example provided in assignment documentation

    """

    # Generate races data
    races = pd.DataFrame(
        {
            "raceId": [1132],
            "year": [2024],
            "round": [12],
            "name": ["British Grand Prix"],
            "date": ["2024-07-07"],
            "time": ["14:00:00"],
        }
    )
    
    # Generate results data
    results = pd.DataFrame(
        {
            "resultId": [1],
            "raceId": [1132],
            "driverId": [1],
            "position": [1],
            "fastestLapTime": ["01:29.4"],
        }
    )
    
    # Pass generated data to build_stats_by_year() to assert final shape
    record = transform.build_stats_by_year(races, results)[2024][0]
    assert record == {
        "Race Name": "British Grand Prix",
        "Race Round": 12,
        "Race Datetime": "2024-07-07T14:00:00.000",
        "Race Winning driverId": 1,
        "Race Fastest Lap": "01:29.4",
    }
