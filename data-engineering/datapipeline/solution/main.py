"""
Entry point: run the F1 stats pipeline (extract -> transform -> load).

"""

import logging
import os
from pipeline import extract, transform, load

# Log level is driven by the LOG_LEVEL env var so it can be changed per
# environment (e.g. INFO in production, DEBUG for incident triage) without a
# code change. Defaults to INFO
# DEBUG is too verbose for normal runs.
# An unrecognised value defaults to INFO rather than crashing the pipeline
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def run() -> None:
    """
    Calls extract functions load_races() and load_results()
    Logs/prints how many records in each extract

    Calls transform function build_stats_by_year()
    Logs/prints how many years produced

    Calls load function write_stats()
    Writes the final JSON output
    Logs/prints filepaths

    """

    races = extract.load_races()
    results = extract.load_results()
    logger.info("Loaded %d races and %d results", len(races), len(results))

    stats_by_year = transform.build_stats_by_year(races, results)
    logger.info("Built stats for %d years", len(stats_by_year))

    written = load.write_stats(stats_by_year)
    for path in written:
        logger.info("Wrote %s", path)


if __name__ == "__main__":
    run()
