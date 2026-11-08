"""Land the Parquet files in Amazon S3 and check the row counts.

  python land_s3.py                 # into the 'demo' bucket
  python land_s3.py --bucket other

Files go to s3://<bucket>/raw/<table>/dt=YYYY-MM-DD/<table>.parquet

boto3 reads AWS_ENDPOINT_URL, which floci-env.ps1 sets to the local emulator.
Without it, boto3 talks to real AWS.
"""

import argparse
import os

import boto3

import lake

parser = argparse.ArgumentParser(description="Land the Parquet files in S3.")
parser.add_argument("--bucket", default="demo")
args = parser.parse_args()

print(f"S3 endpoint: {os.environ.get('AWS_ENDPOINT_URL', 'real AWS')}\n")
s3 = boto3.client("s3")


def list_keys(prefix):
    # S3 returns at most 1,000 keys per call; the paginator fetches the rest.
    pages = s3.get_paginator("list_objects_v2").paginate(Bucket=args.bucket, Prefix=prefix)
    return [obj["Key"] for page in pages for obj in page.get("Contents", [])]


lake.land(
    where=f"s3://{args.bucket}",
    upload=lambda path, key: s3.upload_file(str(path), args.bucket, key),
    list_keys=list_keys,
    download=lambda key: s3.get_object(Bucket=args.bucket, Key=key)["Body"].read(),
)
