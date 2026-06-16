"""
Test Load step at pipeline.load.py

1. 

"""

import json
from pipeline import load

def test_write_stats_creates_one_file_per_year(tmp_path):
    """
    Test that the write_stats() function outputs one file per year
    and ensure that stats_{year}.json is populated using the year key

    """

    # Build input to pass to write_stats()
    stats = {
        2023: [{"Race Name": "A GP", "Race Round": 1}],
        2024: [{"Race Name": "B GP", "Race Round": 1}],
    }

    # pass input to write_stats() function and save in temporary directory
    written = load.write_stats(stats, out_dir=tmp_path)

    # Assert only two json files, one for each year, are output and year variable is used
    assert {p.name for p in written} == {"stats_2023.json", "stats_2024.json"}
    for path in written:
        assert path.exists()


def test_written_file_is_a_valid_json_list_round_trip(tmp_path):
    """
    Generate records and tests None is handled as JSON null

    """

    records = [
        {"Race Name": "A GP", "Race Round": 1, "Race Winning driverId": None},
    ]

    # pass generated records to write_stats() and save in temp directory
    load.write_stats({2024: records}, out_dir=tmp_path)
    # read the file and use json.loads() to parse into Python object
    loaded = json.loads((tmp_path / "stats_2024.json").read_text(encoding="utf-8"))
    # ensure that the top level of the JSON is a list/array
    assert isinstance(loaded, list)
    # ensure that the parsed object does not get manipulated so that final output is what we expect
    assert loaded == records
    # ensure that None type is parsed correctly and JSON null == None
    assert loaded[0]["Race Winning driverId"] is None


def test_creates_output_directory_if_missing(tmp_path):
    """
    Test that the write_stats() function creates the output directory if it doesn't exist
    
    """
    # assign missing filepath to variable
    out_dir = tmp_path / "results"
    # ensure that this directory doesn't exist
    assert not out_dir.exists()
    # attempt to write to this directory with write_stats()
    load.write_stats({2024: []}, out_dir=out_dir)
    # ensure it now exists
    assert out_dir.exists()