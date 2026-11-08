# Builds index.html, the standalone copy of the tracker you can open directly or host (e.g. GitHub Pages).
# app.html is the source: edit that, then run  .\tracker\build.ps1
# (app.html has no <html>/<head> wrapper because the Artifact publisher adds one; this script adds it for the standalone file.)

$src = Join-Path $PSScriptRoot 'app.html'
$out = Join-Path $PSScriptRoot 'index.html'

$head = @'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
'@

$page = $head + "`n" + (Get-Content $src -Raw -Encoding utf8) + "`n</html>`n"
[System.IO.File]::WriteAllText($out, $page, [System.Text.UTF8Encoding]::new($false))
Write-Host "Built $out"
