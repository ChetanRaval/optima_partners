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
