param(
    [Parameter(Mandatory=$false)]
    [string]$BaseUrl = "http://localhost:3000"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Get-Command k6 -ErrorAction SilentlyContinue)) {
    Write-Host "k6 not found. Install k6 and retry."
    exit 1
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportDir = Join-Path $PSScriptRoot "..\\reports\\perf"
$summaryJson = Join-Path $reportDir "k6_summary_$timestamp.json"
$reportHtml = Join-Path $reportDir "k6_report_$timestamp.html"

Write-Host "Running k6 smoke test against $BaseUrl"

k6 run "$PSScriptRoot\\k6_smoke.js" `
  --summary-export "$summaryJson" `
  -e BASE_URL=$BaseUrl

python "$PSScriptRoot\\k6_report.py" "$summaryJson" "$reportHtml"

Write-Host "Summary JSON: $summaryJson"
Write-Host "HTML Report: $reportHtml"
