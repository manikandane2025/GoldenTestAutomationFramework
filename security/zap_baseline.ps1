param(
    [Parameter(Mandatory=$true)]
    [string]$TargetUrl
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is required to run ZAP baseline."
    exit 1
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportDir = Join-Path $PSScriptRoot "..\\reports\\security"
$reportHtml = Join-Path $reportDir "zap_baseline_$timestamp.html"

Write-Host "Running OWASP ZAP baseline scan against $TargetUrl"

docker run --rm -t owasp/zap2docker-stable zap-baseline.py `
    -t $TargetUrl `
    -r (Split-Path $reportHtml -Leaf)

if (Test-Path (Split-Path $reportHtml -Leaf)) {
    Move-Item -Force (Split-Path $reportHtml -Leaf) $reportHtml
}

Write-Host "HTML Report: $reportHtml"
