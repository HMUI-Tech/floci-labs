"""Land the Parquet files in Azure Data Lake Storage Gen2 and check the row counts.

  python land_adls.py                    # into the 'demo' container
  python land_adls.py --container other

Files go to <container>/raw/<table>/dt=YYYY-MM-DD/<table>.parquet

Reads the storage account from AZURE_STORAGE_CONNECTION_STRING. floci-env.ps1
sets it to the local emulator; a real Azure connection string works too.
"""

import argparse
import os
from urllib.parse import urlsplit

import requests
from azure.core.pipeline.transport import RequestsTransport
from azure.storage.filedatalake import DataLakeServiceClient

import lake


def connect():
    """Return (Data Lake client, account name) for the account in the connection string."""
    conn = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not conn:
        raise SystemExit("AZURE_STORAGE_CONNECTION_STRING isn't set. Run floci-env.ps1 first.")
    settings = dict(part.split("=", 1) for part in conn.split(";") if part)
    account = settings["AccountName"]
    blob = urlsplit(settings.get("BlobEndpoint", ""))

    if blob.hostname not in ("localhost", "127.0.0.1"):
        return DataLakeServiceClient.from_connection_string(conn), account  # real Azure

    # The emulator only treats a request as Data Lake (rather than plain Blob) when it's
    # addressed to <account>.dfs.core.windows.net, as in real Azure. So connect to
    # localhost and put that name in the Host header. The address itself stays localhost,
    # so nothing can reach real Azure even if the header were dropped.
    session = requests.Session()
    session.headers["Host"] = f"{account}.dfs.core.windows.net"
    client = DataLakeServiceClient(
        f"{blob.scheme}://{blob.netloc}",
        credential={"account_name": account, "account_key": settings["AccountKey"]},
        transport=RequestsTransport(session=session, session_owner=False),
    )
    return client, account


parser = argparse.ArgumentParser(description="Land the Parquet files in Azure Data Lake Storage.")
parser.add_argument("--container", default="demo")
args = parser.parse_args()

service, account = connect()
# Data Lake calls a container a "file system", and has real folders, unlike plain Blob Storage.
fs = service.get_file_system_client(args.container)


def upload(path, key):
    with open(path, "rb") as f:
        fs.get_file_client(key).upload_data(f, overwrite=True)


lake.land(
    where=f"{account}/{args.container}",
    upload=upload,
    list_keys=lambda prefix: [p.name for p in fs.get_paths(path=prefix.rstrip("/"), recursive=True) if not p.is_directory],
    download=lambda key: fs.get_file_client(key).download_file().readall(),
)
