# PowerShell script to run tests and build the Docker image
# Environment variables: AZURE_DEVOPS_PAT and AZURE_DEVOPS_ORGANIZATION_URL

# Read version from version.txt (located next to this script)
$versionFile = Join-Path $PSScriptRoot "version.txt"
if (-not (Test-Path $versionFile)) {
    Write-Error "version.txt not found. Run bump-version.ps1 to create one, or create it manually."
    exit 1
}
$version = (Get-Content $versionFile -Raw).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Error "Invalid version format in version.txt: '$version'. Expected major.minor.patch"
    exit 1
}
Write-Host "Building version: $version"

Push-Location -Path "./mcp-azure-devops"

# Run tests before building
Write-Host "`nRunning tests..."
& .\.venv\Scripts\python -m pytest -v
if ($LASTEXITCODE -ne 0) {
    Write-Error "Tests failed. Docker image will NOT be built."
    Pop-Location
    exit 1
}
Write-Host "All tests passed.`n"

# Variables
$imageBase  = "mcp-azure-devops"
$imageLatest    = "${imageBase}:latest"
$imageVersioned = "${imageBase}:${version}"

# Build the Docker image with both tags
docker build -t $imageLatest -t $imageVersioned .

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed."
    Pop-Location
    exit 1
}

Write-Host "Docker image built successfully:"
Write-Host "  $imageLatest"
Write-Host "  $imageVersioned"
Write-Host "`nTo run the container, use:"
Write-Host "  docker run -e AZURE_DEVOPS_PAT=your_token -e AZURE_DEVOPS_ORGANIZATION_URL=your_org_url -p 8000:8000 $imageLatest"

Pop-Location
