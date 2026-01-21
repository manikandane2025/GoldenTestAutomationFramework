$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frameworkDir = Resolve-Path (Join-Path $scriptDir "..")
$imageName = "stlc-golden-framework:latest"

Write-Host "Building Docker image: $imageName"
docker build -t $imageName $frameworkDir
Write-Host "Done."
