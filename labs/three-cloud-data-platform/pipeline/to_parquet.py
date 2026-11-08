"""Convert every day of generated JSON lines to Parquet, one file per table per day.

  python to_parquet.py

Reads  data/jsonl/dt=YYYY-MM-DD/<table>.jsonl
Writes data/parquet/<table>/dt=YYYY-MM-DD/<table>.parquet

The date lives in the folder name (`dt=...`), not inside the file. BigQuery,
Athena, Spark and dbt all read it from there, which is called Hive-style partitioning.
"""

import json
from datetime import date, datetime
from decimal import Decimal

import pyarrow as pa
import pyarrow.parquet as pq

from lake import DATA, TABLES

money = pa.decimal128(10, 2)  # exact cents; floats would drift when summing revenue

SCHEMAS = {
    "orders": pa.schema([
        ("order_id", pa.string()),
        ("order_ts", pa.timestamp("us", tz="UTC")),
        ("customer_id", pa.string()),
        ("product_id", pa.string()),
        ("quantity", pa.int32()),
        ("unit_price", money),
        ("status", pa.string()),
    ]),
    "customers": pa.schema([
        ("customer_id", pa.string()),
        ("first_name", pa.string()),
        ("last_name", pa.string()),
        ("email", pa.string()),
        ("signup_date", pa.date32()),
        ("street", pa.string()),
        ("city", pa.string()),
        ("state", pa.string()),
        ("postcode", pa.string()),
        ("updated_at", pa.date32()),
    ]),
    "products": pa.schema([
        ("product_id", pa.string()),
        ("name", pa.string()),
        ("category", pa.string()),
        ("price", money),
    ]),
}


def read_jsonl(path, schema):
    """Read JSON lines, turning text dates and times into real ones and prices into exact decimals."""
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line, parse_float=Decimal)
            for field in schema:
                if pa.types.is_timestamp(field.type):
                    row[field.name] = datetime.fromisoformat(row[field.name])
                elif pa.types.is_date(field.type):
                    row[field.name] = date.fromisoformat(row[field.name])
            rows.append(row)
    return rows


def main():
    days = sorted((DATA / "jsonl").glob("dt=*"))
    if not days:
        raise SystemExit("No generated data yet. Run generate.py first.")

    for day in days:
        counts = []
        for table in TABLES:
            schema = SCHEMAS[table]
            rows = read_jsonl(day / f"{table}.jsonl", schema)
            out = DATA / "parquet" / table / day.name / f"{table}.parquet"
            out.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(pa.Table.from_pylist(rows, schema=schema), out, compression="snappy")
            counts.append(f"{len(rows)} {table}")
        print(f"{day.name}: {', '.join(counts)}")


if __name__ == "__main__":
    main()
