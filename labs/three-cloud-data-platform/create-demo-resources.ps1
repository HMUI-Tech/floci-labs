# Creates a small starter set called "demo" in each local Floci emulator, then lists what exists.
# Safe to run again: anything that already exists is left alone.
#
#   Run:  .\create-demo-resources.ps1
#         .\create-demo-resources.ps1 -Name orders   (use a different name)
#
# Needs the emulators running (docker compose up -d). No cloud CLIs or real accounts needed.

param([string]$Name = 'demo')

$aws   = 'http://localhost:4566'
$azure = 'http://localhost:4577/devstoreaccount1'
$gcp   = 'http://localhost:4588'
$proj  = 'floci-local'
$awsJson = 'application/x-amz-json-1.0'

function Send($method, $url, $headers = @{}, $body = $null, $contentType = 'application/json') {
    $p = @{ Method = $method; Uri = $url; Headers = $headers; TimeoutSec = 15
            SkipHttpErrorCheck = $true; SkipHeaderValidation = $true }
    if ($null -ne $body) { $p.Body = $body; $p.ContentType = $contentType }
    $r = Invoke-WebRequest @p
    # AWS JSON replies use a content type PowerShell treats as binary, so decode it as text.
    $text = if ($r.Content -is [byte[]]) { [Text.Encoding]::UTF8.GetString($r.Content) } else { [string]$r.Content }
    [pscustomobject]@{ StatusCode = [int]$r.StatusCode; Content = $text }
}

function Create($cloud, $what, $method, $url, $headers = @{}, $body = $null, $contentType = 'application/json') {
    $label = '{0,-6} {1,-28}' -f $cloud, $what
    try { $r = Send $method $url $headers $body $contentType }
    catch { Write-Host "$label FAILED: $($_.Exception.Message)" -ForegroundColor Red; return }
    $code = [int]$r.StatusCode
    if ($code -lt 300) { Write-Host "$label ok" -ForegroundColor Green }
    elseif ($code -eq 409 -or $r.Content -match 'AlreadyExists|ResourceInUse|AlreadyOwnedByYou') { Write-Host "$label already exists" }
    else { Write-Host "$label FAILED (HTTP $code): $($r.Content)" -ForegroundColor Red }
}

function Json($obj) { $obj | ConvertTo-Json -Depth 5 -Compress }

Write-Host "Creating '$Name' resources..."

# --- AWS: S3 bucket, SQS queue, DynamoDB table (key: id) ---
Create AWS "S3 bucket $Name"      PUT  "$aws/$Name"
Create AWS "SQS queue $Name"      POST "$aws/" @{ 'X-Amz-Target' = 'AmazonSQS.CreateQueue' } (Json @{ QueueName = $Name }) $awsJson
Create AWS "DynamoDB table $Name" POST "$aws/" @{ 'X-Amz-Target' = 'DynamoDB_20120810.CreateTable' } (Json @{
    TableName            = $Name
    BillingMode          = 'PAY_PER_REQUEST'
    AttributeDefinitions = @(@{ AttributeName = 'id'; AttributeType = 'S' })
    KeySchema            = @(@{ AttributeName = 'id'; KeyType = 'HASH' })
}) $awsJson

# --- Azure (account devstoreaccount1): Blob container, Storage queue, Table ---
$blobVer  = @{ 'x-ms-version' = '2021-08-06' }
$tableVer = @{ 'x-ms-version' = '2019-02-02'; 'DataServiceVersion' = '3.0'; 'Accept' = 'application/json;odata=nometadata' }
Create Azure "Blob container $Name" PUT  "$azure/${Name}?restype=container" $blobVer
Create Azure "Storage queue $Name"  PUT  "$azure-queue/$Name" $blobVer
Create Azure "Table $Name"          POST "$azure-table/Tables" $tableVer (Json @{ TableName = $Name })

# --- GCP (project floci-local): Storage bucket, Pub/Sub topic + subscription ---
Create GCP "Storage bucket $Name"       POST "$gcp/storage/v1/b?project=$proj" @{} (Json @{ name = $Name })
Create GCP "Pub/Sub topic $Name"        PUT  "$gcp/v1/projects/$proj/topics/$Name" @{} '{}'
Create GCP "Pub/Sub subscription $Name" PUT  "$gcp/v1/projects/$proj/subscriptions/$Name" @{} (Json @{ topic = "projects/$proj/topics/$Name" })

# --- List what exists now ---
function Show($cloud, $what, [scriptblock]$get) {
    try { $names = @(& $get) -join ', ' } catch { $names = "(could not list: $($_.Exception.Message))" }
    if (-not $names) { $names = '(none)' }
    '{0,-6} {1,-22} {2}' -f $cloud, $what, $names
}
function XmlNames($r) { [regex]::Matches($r.Content, '<Name>([^<]+)</Name>') | ForEach-Object { $_.Groups[1].Value } }
function Last($path) { ($path -split '/')[-1] }

Write-Host "`nWhat exists now:"
Show AWS   'S3 buckets'            { XmlNames (Send GET "$aws/") }
Show AWS   'SQS queues'            { (Send POST "$aws/" @{ 'X-Amz-Target' = 'AmazonSQS.ListQueues' } '{}' $awsJson).Content | ConvertFrom-Json | ForEach-Object { $_.QueueUrls } | ForEach-Object { Last $_ } }
Show AWS   'DynamoDB tables'       { ((Send POST "$aws/" @{ 'X-Amz-Target' = 'DynamoDB_20120810.ListTables' } '{}' $awsJson).Content | ConvertFrom-Json).TableNames }
Show Azure 'Blob containers'       { XmlNames (Send GET "$azure`?comp=list" $blobVer) }
Show Azure 'Storage queues'        { XmlNames (Send GET "$azure-queue`?comp=list" $blobVer) }
Show Azure 'Tables'                { ((Send GET "$azure-table/Tables" $tableVer).Content | ConvertFrom-Json).value.TableName }
Show GCP   'Storage buckets'       { ((Send GET "$gcp/storage/v1/b?project=$proj").Content | ConvertFrom-Json).items.name }
Show GCP   'Pub/Sub topics'        { ((Send GET "$gcp/v1/projects/$proj/topics").Content | ConvertFrom-Json).topics.name | ForEach-Object { Last $_ } }
Show GCP   'Pub/Sub subscriptions' { ((Send GET "$gcp/v1/projects/$proj/subscriptions").Content | ConvertFrom-Json).subscriptions.name | ForEach-Object { Last $_ } }
