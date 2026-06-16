# Solution README

# Folder Structure
The pipeline reads from `source-data/` and writes to `results/`, both of which live at the `datapipeline/` project root. 

```
datapipeline/
├── source-data/              # Input data (read-only)
│   ├── races.csv             # One row per race (raceId, year, round, name, date, time)
│   └── results.csv           # One row per driver per race (resultId, raceId, driverId, position, fastestLapTime)
│
├── results/                  # Output: one stats_{year}.json file per year (generated)
│   └── stats_2018.json ... stats_2024.json
│
└── solution/                 # The pipeline code and tests
    ├── main.py               # Entry point: orchestrates extract -> transform -> load
    ├── requirements.txt      # Python dependencies
    ├── README.md             # This file
    │
    ├── pipeline/             # The ETL package
    │   ├── __init__.py       # Marks the folder as a Python package
    │   ├── config.py         # Single source of truth: paths, schema, field names, formats
    │   ├── extract.py        # Reads and validates the source CSVs into DataFrames
    │   ├── transform.py      # Builds the per-year winner stats from races + results
    │   └── load.py           # Writes one stats_{year}.json file per year
    │
    └── tests/                # Unit tests (pytest)
        ├── __init__.py
        ├── test_extract.py   # Tests CSV reading, missing-file and bad-column handling
        ├── test_transform.py # Tests the join, winner logic and null handling
        └── test_load.py      # Tests JSON output per year
```

## How to Run
Run everything from the `solution/` directory as this keeps both the pipeline and the tests working without any path manipulation.

```
  cd solution
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  python main.py
  pytest
```

`python main.py` writes the `stats_{year}.json` files into `datapipeline/results/`. `pytest` runs the unit test suite.

### Dependencies and Environment

- **Python:** developed and tested on Python 3.9.6.
- **Dependencies** are pinned to exact versions in `requirements.txt` for reproducibility:
  - `pandas==2.3.3` - used in the extract/transform steps for reading CSVs and joining the data.
  - `pytest==8.4.2` - used to run the testing suite.

### Troubleshooting

- **`ModuleNotFoundError: No module named 'pandas'`** - the virtual environment is not active, or dependencies are not installed. Run `source .venv/bin/activate` then `pip install -r requirements.txt`.
- **`ModuleNotFoundError: No module named 'pipeline'`** - `pytest` is being run from the wrong directory. Run it from `solution/` so the `pipeline` and `tests` packages resolve correctly.
- **`FileNotFoundError: Source file not found: .../source-data/races.csv`** - the `source-data/` folder is missing from the `datapipeline/` project root. The pipeline expects `source-data/races.csv` and `source-data/results.csv` to sit alongside `solution/`.
- **`python: command not found` or wrong version** - use `python3` (or `python3.9`) explicitly. Confirm the active interpreter with `python --version` after activating the venv; it should report 3.9.x.
- **Output not appearing where expected** - the pipeline always writes to `datapipeline/results/` (anchored to the code, not your current directory), so check there rather than your working directory.

# Introduction
Optima has been hired by a motorsport analytics YouTube channel to do rapid analysis of Formula 1 races for their viewers. The requirements for this include developing an automated data pipeline to facilitate transformation and delivery of incoming race statistics immediately following races.

I have developed an automated data pipeline that produces JSON files, as requested by the client, that delivers the race name, race round, the race date and time, the winning driver's identification, and their fastest lap. The solution outputs one JSON file per year where each element in the list contains one race. This output is saved in the `/results` folder named as requested (`stats_{year}.json`).

I have also delivered the stretch goals of implementing unit (and some integration) tests for all functions along with notes relating to productionisation of this data pipeline to a cloud provider, in this case Google Cloud Platform (GCP).

# Assumptions and Interpretation
Due to the relatively brief scope provided for this project, some assumptions have been made in the development of the data pipeline:

1. The JSON output should contain only 1 winner per race, per year
2. The `Race Fastest Lap` element in the output has been interpreted as the **winning** driver's fastest lap rather than the overall fastest lap within the same race. This assumption was made by spot checking the example provided and manually validating that this was the winner's fastest lap within the source data
3. The winning driver is interpreted as `position == 1` in `results.csv`. This has been validated against the source data and is generally expected behaviour, but was not explicitly described in the requirements
4. There are missing results in the 2024 season (round 13-24) which will be included in the final output with nulls for the winner and fastest lap fields
5. Races with no results will be retained with the output containing nulls for winners and fastest lap
6. Although unspecified in the scope, JSON output will be ordered by round number to ensure deterministic sorting and logical ordering
7. In `races.csv` all times are denoted as being in UTC and the output format has been designed such that it matches the specification. While this is an ISO style datetime format, potential downstream consumers of the output would not be able to infer the timezone from the timestamp. If this is required, a slightly different transform would be required

Races with missing results are retained in the final output for data completeness and transparency. They are assigned a null value for the winner and fastest-lap fields rather than being dropped so that the output reflects the full race calendar and makes gaps in the data explicit.

All listed assumptions should be confirmed with the client before delivering the final product to ensure adherence to their requirements and expectations.

# Source Data Overview

Two CSV files in `source-data/`: `races.csv` and `results.csv`.

## Format
- CSV, comma-delimited, with header rows
- Missing values are marked with `null`

## Volume
- `races.csv`: 149 races across 7 seasons (2018-2024)
- `results.csv`: 2,739 driver-race rows

## Relationships and Granularity
- One race has many results (`races` 1 - many `results`).
- `races.csv`: one row per race. Key: `raceId`.
- `results.csv`: one row per driver per race. `raceId` is a foreign key into `races`.
- Join key: `raceId`.

## Schema
**races.csv**

| Column   | Type   | Description                        |
|----------|--------|------------------------------------|
| `raceId` | int    | Unique race identifier             |
| `year`   | int    | Season                             |
| `round`  | int    | Race number within the season      |
| `name`   | string | Race name (e.g. Monaco Grand Prix) |
| `date`   | date   | Race date (`YYYY-MM-DD`)           |
| `time`   | string | Start time (`HH:MM:SS`)            |

**results.csv**

| Column           | Type   | Description                              |
|------------------|--------|------------------------------------------|
| `resultId`       | int    | Unique result identifier                 |
| `raceId`         | int    | Race the result belongs to               |
| `driverId`       | int    | Driver identifier                        |
| `position`       | int    | Finishing position (`1` = winner)        |
| `fastestLapTime` | string | Driver's fastest lap (`MM:SS.s`)         |

## Data Quality
- 12 of 149 races have no results at all (found by comparing distinct `raceId`s across the two files. Only 137 appear in `results`)
- 376 `null` positions and 126 `null` lap times, assumed DNF rather than bad data

# Design Choices

## Technology Used
This project has been developed in Python using the Pandas library. While Pandas is the go to data analysis library for this kind of task, the same result could have been achieved with the Python `stdlib` tools. However, this is the data engineering and data analysis tool of choice, meaning that most developers in these domains are familiar with it, making it easier to collaborate and handover.

Most importantly, Pandas is more performant at scale. For example, the library utilises vectorisation to iterate over large datasets and is more memory-efficient. This means that the pipeline developed here could be scaled to millions of rows and run locally for very little cost before needing to graduate to a cloud provider or distributed system such as Spark.

## ETL vs ELT
The scope for this project outlines a motorspot analytics YouTube channel to do **rapid** analysis of Formula 1 races for their viewers post-race. The scope also describes the exact shape of the data required, hence an ETL (Extract, Transform, Load) framework was chosen. 

Due to the final shape of the data being concretely defined, the most appropriate solution here is to transform the data locally before loading it into the destination in the format requested. Data is extracted from the source data provided, transformed by filtering and aggregating the data, and the final JSON files are loaded into the destination directory.

In this instance ETL is cheap/free and extremely fast since the scale of data here can be processed in memory, but there are some limitations. Since we only land the transformed data in the destination anything that isn't output is effectively discarded without additional pipelines being created if new specifications are received from the client.

### Reasons to Move to ELT
If this project were to scale to wanting more granular F1 race data with additional data points, changing schemas, and no singular defined final data shape, ELT (Extract, Load, Transform) would be the approach to take. It's cheaper and faster to load all source data into a warehouse rather than hosting it on a local machine, preserve all raw data, and handle transformations within a cloud provider such as AWS/GCP/Azure.

The ELT pattern allows the consumer to get bespoke cuts and aggregations of the data for different audiences. In the ETL pattern we produce one cut, but in reality the same race and results data could be cut in many different ways that the viewers of the YouTube channel would be interested in (e.g. per driver career stats, per track stats, overall fastest lap leaderboards). This can be solved for by creating cleaned staging layer in your data warehouse once it's loaded (using dbt, for example) and then building on top of that.

Finally, this pipeline currently runs as a batch job and could be scheduled to run end-to-end once a day, for example. However, if the YouTube channel wants it immediately post-race or the scope changes to the client needing the data after each lap is completed, or even in real-time then running the entire pipeline as a batch at that frequency becomes inefficient. In the ELT pattern, we could switch to to an event-driven or streaming model where a trigger could be set up to run the transform logic when new data lands providing a great deal of flexibility to the data engineers and the client.

## Scalability, Performance, and Cost
Currently this is an extremely small dataset and could scale to millions of rows as long as the memory on a local machine could process it, but there are considerations to make if the requirements and data size were to scale significantly. As mentioned above, the pivot to ELT would be prioritised alongside using a platform such as Spark for distributed compute. Other considerations would include partitioning the data and incremental loads if the granularity and frequency of data changed. 

At the current scale, cost is not a consideration but if the data volume and frequency increased significantly, moving to a cloud provider would be required ultimately incurring costs. Depending on the scale of the data, an assessment would need to be made regarding costs for jobs run in the cloud and orchestration etc. 

## Error Handling and Testing (Stretch Goal)

### Implemented Testing
Errors and failures are caught at the boundary on the extract step so that bad data is never propagated to the transform step. Missing files, empty/corrupt files, and missing/renamed columns are tested for. 

The transform tests handle data-quality and business logic such as races with no results retain nulls, missing times default to `00:00:00`, and that the output of the transformation doesn't drop or duplicate any races. 

Load tests also ensure that requirements are met, such as only writing one file per year, null values in the output are handled correctly, and that the output directory is created if it is missing.

### Testing Gaps
The tests implemented here are simple and quite granular due to the scale of the project. However, if this solution needed to scale some testing considerations I would make include:

- Data-quality checks on every run (null frequency, uniqueness of data, row-count vs previous runs, ensuring that only one instance of `position == 1` in each race)
- Performance and scaling tests to ensure the pipeline stays within the agreed upon memory/compute/time budget
- Idempotency and data recovery in the case that ingestion fails
- Logging and observability such as metrics/alerts on row counts and null frequency

Currently, I am enforcing schema and output shape correctness by manually defining an expected value in `test_transform.test_matches_assignment_example_shape()` which allows me to validate the output at this small scale, however if more fields were added or requirements changed, this would mean significant manual work to update these tests. In a production system I would declare a centralised schema by using `Pydantic` models and consider input/output schema validation using a package such as `Pandera`. 

# Maintainability, Collaboration, and Handover
I have implemented a single source of truth for paths, schemas, and expected output formatting in `config.py` improving readability of the code and allowing a developer to easily rename and swap out metrics in the pipeline.

A scenario that I anticipate occurring is that the client might want a new set of metrics added to the output before the next race on Sunday. What considerations would I make in order to ensure that columns can be added or removed dynamically by any engineer and if a failure occurs the pipeline keeps running? 

While it is over-engineered for this particular assignment, I have rudimentally solved for this by creating an output metric registry in `transform.py` and a corresponding test. This pattern allows collaborators, in isolation, to add metrics to the registry which then cascade to downstream functions.

Something not provided here but would in a real-world scenario is comprehensive reference documentation. This would enable a smooth handover to other data engineers and analysts and empower clients to be self-reliant, ultimately optimising the time Optima spends providing aftercare.

# DevOps
Logging has been implemented in `main.py` at the default INFO level with the option to launch with any other logger level names (DEBUG, WARNING, ERROR, CRITICAL) for this pipeline. The logging in this case has simple outputs such as the number of records in each CSV, how many years of data produced, and the filepaths in the output directory. If this solution needed to scale and was deployed on a cloud provider, I would consider switching to structured JSON logging so these logs could be timestamped and stored appropriately for auditing purposes along with WARNING and ERROR based triggers that send notifications via email to relevant parties. 

No other logging has been implemented here but some additional considerations include data-quality logging such as races with no matching results logs a warning but does not destroy the data pipeline. A missing or corrupt input file logging an ERROR that causes the pipeline to fail would allow an engineer to respond quickly. Additionally, recording counts as metrics such as records per year, this run vs last run etc., would allow the creation of a warning or alert for unexpected values even if the pipeline is not failing.

No CI/CD considerations have been made in this project, however merges into Git should be gated on tests using something like GitHub Actions or Gitlab Pipelines. Dependencies have been pinned to exact versions in `requirements.txt` which allows reproducibility locally and in cloud builds so that an update to a dependency doesn't suddenly break the entire pipeline.

# Cloud Deployment Notes (Stretch Goal)
As mentioned in this documentation, if this project was to scale it would need to be deployed to a cloud provider. For this example, I have chosen to create notes regarding to a deployment in Google Cloud Platform (GCP) as this is the tool that I am most familiar with.

## Pipeline
Moving to the cloud provider would allow us to pivot to an ELT pattern using tools such as Google Cloud Storage buckets with a Cloud Run job. In this simple example, the file would land in the GCS bucket, a Pub/Sub event trigers a Cloud Run job to load the raw data into BigQuery and then run a `dbt run` that executes the required transformation(s) in BigQuery and also runs dbt testing. On success we can trigger an email notification to the consumer.

This simple ELT pipeline can be done on the same Cloud Run job in sequence for simplicity, but if more transformations are required down the track, then a tool such as Cloud Composer (AirFlow) could be used to orchestrate steps along the way with explicit logging and monitoring. Some warnings that we could monitor for are data quality issues such as unexpected columns or errors for columns that are required (e.g. Fastest Lap Time) but aren't present. 

## Client Considerations
Solving for idempotency in this pipeline to ensure that the same race arriving twice doesn't break the final output could involve having a per-ingestion view that generates a new output with a run ID and datetime stamp. Something to clarify with the client is that if the race data develops, is it safe to assume that we should be using the newest data for each race in the final output or only the results that were available immediately after the race finished?

GDPR considerations should be made when handling data that could be sensitive. In this case, there is no sensitive data, but regulatory data residency issues should be noted. If there was PII, the data should be based within the jurisdiction where the subjects of the data are, which has the added benefit of reducing the latency for EU consumers of the data.

## Minimum Viable Product
If this project needed to be deployed to the client as quickly as possible, the goal would be to design a solution that is reliable and schema-safe. The orchestration mentioned above could be deferred until the client's scope increases. The MVP for this example keeps the existing Python ETL pattern and wraps it in GCP services.

**Architecture:**

1. **GCS** - source CSVs are uploaded to a Google Cloud Storage (GCS) bucket. This is the single ingestion point and gives us a durable, versioned copy of every raw file for replay/audit.
2. **Cloud Run** - an event on the bucket fires a Pub/Sub message that invokes a Cloud Run job running this pipeline in a Docker container. 
3. **Transform** - the pipeline runs extract -> transform -> load as today, reading from GCS and writing the `stats_{year}.json` output back to a results bucket (or to BigQuery if the client wants queryable data).
4. **Notify** - on success/failure, a structured log entry triggers a Cloud Monitoring alert (email/Slack) so the client knows each race's stats are live.

- **Input Schema** - validate the source CSVs on extract against an explicit schema (column names, data types, nullability) using a tool such as Pandera. A new/renamed/missing column fails the run with a clear error instead of breaking downstream processes.
- **Output Schema** - validate the transformed records against the agreed JSON shape before load, since that shape is a client contract. This replaces the manually-maintained `test_transform` example check with an enforced runtime schema.

This solution would have a minimal Git CI/CD pipeline that runs the testing, writes to the bucket would have a run ID and load datetime for idempotency safety, structured JSON logging, and minimal costs. 

# Use of AI in Development
While this assignment could be solved at a high level by passing it to an LLM or made difficult to solve by not using any assistance, I decided to land in the middle of that spectrum. I use AI in day-to-day development to brainstorm, prototype ideas, and ultimately create specifications to solve business problems. My workflow involves prompting the AI in small, logical increments of functionality rather than large monolithic pieces of work. As a sidenote, this also applies to my Git strategy where code is committed in small, logical chunks with thorough commit messages to preserve the ability to roll back to previous versions of the code. 

I accept full responsibility for the code and solution design and therefore ensure that I am generating and deploying code that I understand. In this case, I used AI to create test cases, audit my Python scripts to ensure they align with best practices, and to collaborate on writing the specification and implementing the metrics registry mentioned earlier.

In a real workflow that uses AI assisted coding, I would create a comprehensive `CLAUDE.md` to ensure that the technical and business rules of the project are always adhered to. For a very cursory example, I would include items such as:


```
CLAUDE.md

- `config.py` is the single source of truth for paths, schemas, field names, formats. Never hardcode values in the extract/transform/load steps
- Winner = `position == 1`. Race fastest lap is the winner's fastest lap, not the race minimum
- Every race appears in output exactly once - never drop or duplicate.
- Races with no results are RETAINED with null winner/lap (left join, by design).
- Missing time - defaults to `00:00:00`. Output sorted by `round`.
- New output metrics go through the registry in `transform.py`, not ad-hoc.
- Don't add dependencies beyond pandas/pytest without a prompting the user.
- Don't change the JSON output shape - it's a client contract (see test_transform).
```



