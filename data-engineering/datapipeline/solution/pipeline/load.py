"""
Load step: write one stats_{year}.json file per year.

"""

import json
from pathlib import Path
from . import config

# Write each year's records to results/stats_{year}.json and return the filepath
def write_stats(stats_by_year: dict[int, list[dict]], out_dir: Path = config.RESULTS_DIR) -> list[Path]:
    """
    Parameters:
    stats_by_year: dict mapping year to a list of record dicts for that year.
    Created by transform.build_stats_by_year()

    out_dir: output directory defaulting to the filepath defined in config.py

    list[Path]: returns a list of the file paths it wrote
    """
    
    # create the output directory if it doesn't exist
    out_dir.mkdir(parents=True, exist_ok=True)
    # empty list to log filepaths that have bene written
    written: list[Path] = []
    # loop over each (year, records) par in the input dictionary
    for year, records in stats_by_year.items():
        # build the output filepath with the output filename derived from config.py
        path = out_dir / config.OUTPUT_FILENAME.format(year=year)
        # open the file for writing
        with path.open("w", encoding="utf-8") as f:
            # dump the json record into the file with pretty printing and handle non-ASCII characters
            # non-ASCII characters handled here due to F1 lineup containing many accented names
            json.dump(records, f, indent=2, ensure_ascii=False)
        # append filepath to written list
        written.append(path)
    # return all written paths
    return written
