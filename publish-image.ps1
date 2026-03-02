# Read version from version.txt (located next to this script)
$versionFile = Join-Path $PSScriptRoot "version.txt"
if (-not (Test-Path $versionFile)) {
    Write-Error "version.txt not found."
    exit 1
}
$version = (Get-Content $versionFile -Raw).Trim()
if ($version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Error "Invalid version format in version.txt: '$version'. Expected major.minor.patch"
    exit 1
}

# Set variables
$GHCR_USER = "movesny"
$GHCR_TOKEN = Get-Content -Path "github_token.txt" -Raw
$IMAGE_LOCAL = "mcp-azure-devops:latest"
$IMAGE_REMOTE_LATEST    = "ghcr.io/movesny/mcp-azure-devops:latest"
$IMAGE_REMOTE_VERSIONED = "ghcr.io/movesny/mcp-azure-devops:${version}"

# Login to GitHub Container Registry
$GHCR_TOKEN | docker login ghcr.io -u $GHCR_USER --password-stdin

# Tag and push :latest
docker tag $IMAGE_LOCAL $IMAGE_REMOTE_LATEST
docker push $IMAGE_REMOTE_LATEST

# Tag and push versioned
docker tag $IMAGE_LOCAL $IMAGE_REMOTE_VERSIONED
docker push $IMAGE_REMOTE_VERSIONED

Write-Host "Published:"
Write-Host "  $IMAGE_REMOTE_LATEST"
Write-Host "  $IMAGE_REMOTE_VERSIONED"
