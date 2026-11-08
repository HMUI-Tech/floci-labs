"""Land the Parquet files in Google Cloud Storage and check the row counts.

  python land_gcs.py                 # into the 'demo' bucket
  python land_gcs.py --bucket other

Files go to gs://<bucket>/raw/<table>/dt=YYYY-MM-DD/<table>.parquet
"""

import argparse
import os

from google.cloud import storage

import lake

parser = argparse.ArgumentParser(description="Land the Parquet files in Cloud Storage.")
parser.add_argument("--bucket", default="demo")
args = parser.parse_args()

client = storage.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT", "floci-local"))
bucket = client.bucket(args.bucket)

lake.land(
    where=f"gs://{args.bucket}",
    upload=lambda path, key: bucket.blob(key).upload_from_filename(path),
    list_keys=lambda prefix: [b.name for b in client.list_blobs(bucket, prefix=prefix)],
    download=lambda key: bucket.blob(key).download_as_bytes(),
)
