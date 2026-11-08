"""Shared steps for landing the Parquet files in any cloud's storage.

Each cloud script (land_gcs.py, land_adls.py, land_s3.py) only says how to
upload, list and download in that cloud. Everything else lives here, so the
three are easy to compare side by side.
"""

import io
from pathlib import Path

import pyarrow.parquet as pq

DATA = Path(__file__).parent / "data"
TABLES = ("orders", "customers", "products")
PREFIX = "raw/"


def local_files():
    """Every Parquet file on disk, with the object key it gets in the cloud."""
    for path in sorted((DATA / "parquet").glob("*/dt=*/*.parquet")):
        yield path, PREFIX + path.relative_to(DATA / "parquet").as_posix()


def generator_rows(key):
    """How many rows generate.py wrote for this table and day, or None if that day isn't on disk."""
    _, table, dt, _ = key.split("/")  # raw/<table>/dt=<date>/<table>.parquet
    path = DATA / "jsonl" / dt / f"{table}.jsonl"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def land(where, upload, list_keys, download):
    """Upload every local file, then list what's really in storage and check each row count.

    upload(path, key)   send one local file to `key`
    list_keys(prefix)   names of everything stored under `prefix`
    download(key)       the bytes stored at `key`
    """
    files = list(local_files())
    if not files:
        raise SystemExit("No Parquet files yet. Run generate.py, then to_parquet.py.")

    print(f"Uploading {len(files)} files to {where} ...", end=" ", flush=True)
    for path, key in files:
        upload(path, key)
    print("done")

    print(f"\nChecking {where}/{PREFIX} against the generator")
    print(f"  {'file':<45} {'generator':>9} {'stored':>7}")
    stored_keys = sorted(k for k in list_keys(PREFIX) if k.endswith(".parquet"))
    bad = 0
    for key in stored_keys:
        expected = generator_rows(key)
        stored = pq.ParquetFile(io.BytesIO(download(key))).metadata.num_rows
        if expected is None:
            status = "not generated on this machine"
        elif expected == stored:
            status = "ok"
        else:
            status, bad = "MISMATCH", bad + 1
        print(f"  {key:<45} {expected if expected is not None else '-':>9} {stored:>7}  {status}")

    # A file that failed to upload isn't in the listing, so look for it explicitly.
    missing = sorted({key for _, key in files} - set(stored_keys))
    for key in missing:
        print(f"  {key:<45} {generator_rows(key):>9} {'-':>7}  MISSING")
    bad += len(missing)

    checked = len(stored_keys) + len(missing)
    if bad:
        raise SystemExit(f"\n{bad} of {checked} files don't match the generator.")
    days = len({k.split("/")[2] for k in stored_keys})
    print(f"\nAll {len(stored_keys)} files match the generator ({days} days of {', '.join(TABLES)}).")
