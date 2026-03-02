# Increments the version number in version.txt
# Usage: .\bump-version.ps1 [-Part patch|minor|major]
# Default: bumps the patch number

param(
    [ValidateSet("patch", "minor", "major")]
    [string]$Part = "patch"
)

$versionFile = Join-Path $PSScriptRoot "version.txt"

if (-not (Test-Path $versionFile)) {
    Write-Error "version.txt not found at $versionFile"
    exit 1
}

$currentVersion = (Get-Content $versionFile -Raw).Trim()

if ($currentVersion -notmatch '^\d+\.\d+\.\d+$') {
    Write-Error "Invalid version format in version.txt: '$currentVersion'. Expected major.minor.patch"
    exit 1
}

$parts = $currentVersion.Split('.')
[int]$major = $parts[0]
[int]$minor = $parts[1]
[int]$patch = $parts[2]

switch ($Part) {
    "major" {
        $major++
        $minor = 0
        $patch = 0
    }
    "minor" {
        $minor++
        $patch = 0
    }
    "patch" {
        $patch++
    }
}

$newVersion = "$major.$minor.$patch"
Set-Content -Path $versionFile -Value $newVersion -NoNewline

Write-Host "Version bumped: $currentVersion -> $newVersion"
