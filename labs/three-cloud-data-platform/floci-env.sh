# Points AWS, Azure and GCP tools in this shell at the local Floci emulators.
#
#   Turn on:   source ./floci-env.sh
#   Turn off:  source ./floci-env.sh --off
#
# Use `source` (or `.`), not `bash floci-env.sh`, so the variables stay in your shell.
# On Windows PowerShell, use floci-env.ps1 instead.

_floci_vars="AWS_ENDPOINT_URL AWS_DEFAULT_REGION AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
GOOGLE_CLOUD_PROJECT PUBSUB_EMULATOR_HOST FIRESTORE_EMULATOR_HOST DATASTORE_EMULATOR_HOST
SECRET_MANAGER_EMULATOR_HOST FIREBASE_AUTH_EMULATOR_HOST STORAGE_EMULATOR_HOST
AZURE_STORAGE_CONNECTION_STRING"

if [ "$1" = "--off" ]; then
    for _v in $_floci_vars; do unset "$_v"; done
    echo "Floci variables removed. Tools now talk to the real clouds again."
else
    # AWS (port 4566). Floci accepts any non-empty keys.
    export AWS_ENDPOINT_URL=http://localhost:4566
    export AWS_DEFAULT_REGION=us-east-1
    export AWS_ACCESS_KEY_ID=test
    export AWS_SECRET_ACCESS_KEY=test

    # GCP (port 4588). The SDKs skip sign-in when these are set.
    export GOOGLE_CLOUD_PROJECT=floci-local
    export PUBSUB_EMULATOR_HOST=localhost:4588
    export FIRESTORE_EMULATOR_HOST=localhost:4588
    export DATASTORE_EMULATOR_HOST=localhost:4588
    export SECRET_MANAGER_EMULATOR_HOST=localhost:4588
    export FIREBASE_AUTH_EMULATOR_HOST=localhost:4588
    export STORAGE_EMULATOR_HOST=http://localhost:4588

    # Azure Storage (port 4577). Floci doesn't check the key, but the SDKs need a
    # base64 value to sign with, so this is just "test" in base64.
    export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=dGVzdA==;BlobEndpoint=http://localhost:4577/devstoreaccount1;QueueEndpoint=http://localhost:4577/devstoreaccount1-queue;TableEndpoint=http://localhost:4577/devstoreaccount1-table;"

    echo "Tools in this shell now point at Floci:"
    echo "  AWS   -> http://localhost:4566"
    echo "  Azure -> http://localhost:4577  (account: devstoreaccount1)"
    echo "  GCP   -> http://localhost:4588  (project: floci-local)"
fi
unset _floci_vars _v
