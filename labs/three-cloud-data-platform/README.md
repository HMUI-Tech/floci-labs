# Three-cloud data platform

> Learn data engineering on AWS, Azure and GCP side by side, on your own laptop: one Compose file runs all three Floci emulators, a pipeline lands the same data in S3, Azure Data Lake and Cloud Storage, and a six-month tracker walks you through it.

## Built on Floci

This lab exists because of [Floci](https://floci.io): free, MIT-licensed emulators for [AWS](https://github.com/floci-io/floci), [Azure](https://github.com/floci-io/floci-az) and [GCP](https://github.com/floci-io/floci-gcp). They make it possible to learn three clouds without an account, a credit card or a surprise bill. Thank you to the Floci maintainers and contributors, and to [floci-labs](https://github.com/floci-io/floci-labs) for giving projects like this a home. If this lab helps you, go and star their repos.

## How this differs from the Floci repos

Nothing here changes Floci. The Floci repos are the emulators themselves; this lab is a learning kit that runs on top of their published Docker images.

| | Floci repos (`floci`, `floci-az`, `floci-gcp`) | This lab |
|---|---|---|
| What it is | Emulator source: servers that answer each cloud's API | A ready-to-run learning kit that uses those emulators |
| How you start it | One emulator per `docker run` | `docker compose up -d` starts all three on one network, with state saved between restarts |
| Pointing tools at it | Set the endpoint variables yourself | `floci-env.ps1` / `floci-env.sh` sets every AWS, Azure and GCP SDK variable in one go |
| Example data | None | A seeded orders generator, Parquet conversion, and landing scripts for all three clouds that check every row count |
| Learning path | Docs per service | A six-month tracker (data engineering, integration, architecture) with step-by-step guides for the first block |

## What it shows

- Running AWS, Azure and GCP emulators together, with saved state and a shared Docker network
- Generating a repeatable week of shop orders (same date, same data, every time)
- Converting it to typed Parquet with Hive-style `dt=YYYY-MM-DD` partitions and exact decimal prices
- Landing the same files in **Cloud Storage**, **Azure Data Lake Storage Gen2** and **S3**, then proving it worked by reading every file back and comparing row counts with the generator
- How the three storage services differ when you write the same code against each

## Stack

- **Runtime:** Python 3.11+, Docker, PowerShell 7 for the demo-resources script (it runs on macOS and Linux too)
- **Libraries:** Faker, pyarrow, google-cloud-storage, google-cloud-pubsub, azure-storage-file-datalake, boto3
- **Services:** S3, SQS, DynamoDB · Blob Storage / ADLS Gen2, Queue Storage, Table Storage · Cloud Storage, Pub/Sub
- **Images:** `floci/floci`, `floci/floci-az`, `floci/floci-gcp` (all `latest`)

## Run it

Start the emulators and create a `demo` bucket, queue and table in each cloud:

```bash
git clone https://github.com/floci-io/floci-labs.git
# Not in floci-io/floci-labs yet? Clone the branch it was built on instead:
# git clone -b lab/three-cloud-data-platform https://github.com/HMUI-Tech/floci-labs.git
cd floci-labs/labs/three-cloud-data-platform
docker compose up -d
pwsh ./create-demo-resources.ps1
```

| Cloud | Address | Web console |
|---|---|---|
| AWS | http://localhost:4566 | http://localhost:4566/_floci/ui |
| Azure | http://localhost:4577 (account `devstoreaccount1`) | http://localhost:4577/_floci/ui |
| GCP | http://localhost:4588 (project `floci-local`) | none |

Then run the pipeline. On Windows (PowerShell):

```powershell
cd pipeline
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
. ..\floci-env.ps1

python gcp_check.py
python generate.py --date 2026-11-02 --days 7
python to_parquet.py
python land_gcs.py
python land_adls.py
python land_s3.py
```

On macOS or Linux:

```bash
cd pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
source ../floci-env.sh

python gcp_check.py
python generate.py --date 2026-11-02 --days 7
python to_parquet.py
python land_gcs.py
python land_adls.py
python land_s3.py
```

Each `land_*.py` script ends with:

```
All 21 files match the generator (7 days of orders, customers, products).
```

### The learning tracker

Open `tracker/index.html` in your browser. It works offline. It lays out 26 weeks across AWS, Azure and GCP, and each task in the first block has a **How to do it** section with commands, expected output and an exercise. Your ticks are saved in your browser; use **Copy backup** in Settings to move them elsewhere.

`tracker/app.html` is the source. After editing it, run `tracker/build.ps1` to rebuild `index.html`.

## How it works

- **`floci-env.ps1` / `floci-env.sh`** set the standard SDK variables (`AWS_ENDPOINT_URL`, `STORAGE_EMULATOR_HOST`, `PUBSUB_EMULATOR_HOST`, `AZURE_STORAGE_CONNECTION_STRING` and friends). The Python code never mentions the emulator, so the same scripts would run against the real clouds.
- **`generate.py`** seeds every random choice from fixed text such as `orders-2026-11-02`, so a date always produces the same orders. A quarter of customers move house on a set day, which later feeds a customer-history (SCD Type 2) exercise.
- **`to_parquet.py`** writes an explicit schema per table. Prices are `decimal(10,2)` so revenue sums are exact to the cent.
- **`lake.py`** holds the upload-then-verify steps once. Each `land_*.py` only supplies upload, list and download for its cloud, so you can compare the three side by side. The check lists what's really in storage, reads each Parquet footer for the row count, and also reports any file that never arrived.
- **Azure Data Lake gotcha:** `floci-az` only treats a request as Data Lake (rather than plain Blob) when it's addressed to `<account>.dfs.core.windows.net`, like real Azure. Sent to plain `localhost:4577`, append, flush and list return `501 Not Implemented`. `land_adls.py` connects to localhost and sets that name in the `Host` header. The address stays localhost, so nothing can reach the real Azure endpoint, even by accident.

## Try changing...

- Add a `channel` field (`web`, `app`, `store`) to orders in `generate.py` and to the schema in `to_parquet.py`, then check the output still repeats exactly.
- Generate one more day (`--date 2026-11-09`), convert and land it. The check should report 24 files over 8 days.
- Make one upload fail on purpose (for example, skip the orders file for one day in a script's `upload` function) and watch the check report it as `MISSING`.
- Write down three differences between Cloud Storage, Data Lake and S3 that you noticed while reading the three `land_*.py` scripts.

## Credentials

Everything here is a dummy value: AWS uses `test`/`test`, GCP skips sign-in, and the Azure account key is `dGVzdA==` (base64 for "test"). Floci doesn't check keys.

## Author

[HMUI-Tech](https://github.com/HMUI-Tech)
