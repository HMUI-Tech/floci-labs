"""Check that Python can reach GCP: list the Cloud Storage buckets and Pub/Sub topics.

Load the lab's floci-env.ps1 (Windows) or floci-env.sh (macOS/Linux) first to
point the clients at the local emulator. Without it, they talk to real GCP.

  python gcp_check.py
"""

import os

from google.cloud import pubsub_v1, storage

project = os.environ.get("GOOGLE_CLOUD_PROJECT", "floci-local")
storage_host = os.environ.get("STORAGE_EMULATOR_HOST")
pubsub_host = os.environ.get("PUBSUB_EMULATOR_HOST")

print(f"Project:       {project}")
print(f"Cloud Storage: {storage_host or 'real GCP'}")
print(f"Pub/Sub:       {pubsub_host or 'real GCP'}")
print()

# With STORAGE_EMULATOR_HOST set, the client skips sign-in and talks to the emulator.
gcs = storage.Client(project=project)
buckets = [b.name for b in gcs.list_buckets()]
print("Buckets:      ", ", ".join(buckets) or "(none)")

# With PUBSUB_EMULATOR_HOST set, the client opens a plain (non-TLS) gRPC connection to it.
publisher = pubsub_v1.PublisherClient()
topics = [t.name.rsplit("/", 1)[-1] for t in publisher.list_topics(project=f"projects/{project}")]
print("Topics:       ", ", ".join(topics) or "(none)")

subscriber = pubsub_v1.SubscriberClient()
with subscriber:
    subs = [s.name.rsplit("/", 1)[-1] for s in subscriber.list_subscriptions(project=f"projects/{project}")]
print("Subscriptions:", ", ".join(subs) or "(none)")

missing = [what for what, names in (("bucket", buckets), ("topic", topics)) if "demo" not in names]
if missing:
    raise SystemExit(f"\nNo 'demo' {' or '.join(missing)} found. Run create-demo-resources.ps1 first.")
print("\nOK: the 'demo' bucket and topic are both there.")
