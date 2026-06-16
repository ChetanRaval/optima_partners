"""
Paths, schema and formatting constants for the pipeline.

"""


from pathlib import Path

# datapipeline/  (parent of solution/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Declare paths. These can be changed in this file and cascade through to ETL steps
SOURCE_DIR = PROJECT_ROOT / "source-data"
RACES_CSV = SOURCE_DIR / "races.csv"
RESULTS_CSV = SOURCE_DIR / "results.csv"
RESULTS_DIR = PROJECT_ROOT / "results"

# Expected source columns (used to validate input).
RACES_COLUMNS = ["raceId", "year", "round", "name", "date", "time"]
RESULTS_COLUMNS = ["resultId", "raceId", "driverId", "position", "fastestLapTime"]

# Columns that must be whole numbers. On extract these are stripped of stray
# whitespace and coerced to numbers so that the raceId join key lines up even
# if a value arrives as " 123", and non-numeric values like a "DNF" position
# become null rather than breaking the winner comparison or the join.
RACES_NUMERIC_COLUMNS = ["raceId", "year", "round"]
RESULTS_NUMERIC_COLUMNS = ["resultId", "raceId", "driverId", "position"]

# fastestLapTime must look like MM:SS.s (e.g. "01:29.4") as per the example provided. 
#V alidated in extract so that a value in the wrong unit/format (e.g. seconds "92.4") fails
FASTEST_LAP_COLUMN = "fastestLapTime"
FASTEST_LAP_PATTERN = r"^\d{1,2}:\d{2}\.\d$"

# JSON output field names
RACE_NAME = "Race Name"
RACE_ROUND = "Race Round"
RACE_DATETIME = "Race Datetime"
RACE_WINNING_DRIVER_ID = "Race Winning driverId"
RACE_FASTEST_LAP = "Race Fastest Lap"

# Winning driver position definition. 
# Added here as this can be changed easily if spec changes
WINNING_POSITION = 1

# Race datetime format and fallback as per spec
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.000"
DEFAULT_TIME = "00:00:00"

# Output filename pattern, e.g. stats_2024.json.
OUTPUT_FILENAME = "stats_{year}.json"
