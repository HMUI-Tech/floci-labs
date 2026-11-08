# Points AWS, Azure and GCP tools in this PowerShell window at the local Floci emulators.
#
#   Turn on:   . .\floci-env.ps1
#   Turn off:  . .\floci-env.ps1 -Off
#
# The leading dot matters: it keeps the variables in your current window.
# Only this window is affected; close it and everything goes back to normal.
# On macOS or Linux, use floci-env.sh instead.

param([switch]$Off)

$vars = [ordered]@{
    # AWS (port 4566). Floci accepts any non-empty keys.
    AWS_ENDPOINT_URL      = 'http://localhost:4566'
    AWS_DEFAULT_REGION    = 'us-east-1'
    AWS_ACCESS_KEY_ID     = 'test'
    AWS_SECRET_ACCESS_KEY = 'test'

    # GCP (port 4588). The SDKs skip sign-in when these are set.
    GOOGLE_CLOUD_PROJECT         = 'floci-local'
    PUBSUB_EMULATOR_HOST         = 'localhost:4588'
    FIRESTORE_EMULATOR_HOST      = 'localhost:4588'
    DATASTORE_EMULATOR_HOST      = 'localhost:4588'
    SECRET_MANAGER_EMULATOR_HOST = 'localhost:4588'
    FIREBASE_AUTH_EMULATOR_HOST  = 'localhost:4588'
    STORAGE_EMULATOR_HOST        = 'http://localhost:4588'

    # Azure Storage (port 4577). Floci doesn't check the key, but the SDKs need a
    # base64 value to sign with, so this is just "test" in base64.
    AZURE_STORAGE_CONNECTION_STRING = 'DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=dGVzdA==;' +
        'BlobEndpoint=http://localhost:4577/devstoreaccount1;' +
        'QueueEndpoint=http://localhost:4577/devstoreaccount1-queue;' +
        'TableEndpoint=http://localhost:4577/devstoreaccount1-table;'
}

if ($Off) {
    foreach ($name in $vars.Keys) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }
    Write-Host 'Floci variables removed. Tools now talk to the real clouds again.'
} else {
    foreach ($name in $vars.Keys) { Set-Item "Env:$name" $vars[$name] }
    Write-Host 'Tools in this window now point at Floci:'
    Write-Host '  AWS   -> http://localhost:4566'
    Write-Host '  Azure -> http://localhost:4577  (account: devstoreaccount1)'
    Write-Host '  GCP   -> http://localhost:4588  (project: floci-local)'
}
