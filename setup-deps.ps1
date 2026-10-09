param([switch]$UseClassicSdl, [switch]$UseUpstreamSdl)

$ErrorActionPreference = 'Stop'
if ($UseClassicSdl -and $UseUpstreamSdl) { throw 'Choose one SDL runtime' }

$Organization = "moonlight-stream"
$PrebuiltRepo = "moonlight-qt-deps"
$TargetDir = Join-Path $PSScriptRoot "libs\windows"
$Assets = @("windows-x64.zip", "windows-ARM64.zip")
$Tag = "v19"

# This script only clears the dependency directory inside this checkout.
$TaskExpectedTarget = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'libs\windows'))
if ([IO.Path]::GetFullPath($TargetDir) -ne $TaskExpectedTarget) { throw 'Unexpected dependency target' }

if (Test-Path $TargetDir) {
    Write-Host "Cleaning target directory..." -ForegroundColor Cyan
    Get-ChildItem -LiteralPath $TargetDir -Force | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
    }
} else {
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}

foreach ($AssetName in $Assets) {
    $Url = "https://github.com/$Organization/$PrebuiltRepo/releases/download/$Tag/$AssetName"
    $ArchivePath = Join-Path $env:TEMP $AssetName

    Write-Host "Downloading $AssetName..." -ForegroundColor Cyan
    curl.exe -s -L -f -o "$ArchivePath" "$Url"
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    Write-Host "Extracting $AssetName..." -ForegroundColor Cyan
    Expand-Archive -Path $ArchivePath -DestinationPath $TargetDir -Force
    Remove-Item $ArchivePath
}

if ($UseClassicSdl) {
    # Only Windows x64 is covered by the JIS runtime workaround and live test.
    & (Join-Path $PSScriptRoot 'scripts\install-classic-sdl.ps1') -RuntimeDirectory (Join-Path $TargetDir 'lib\x64')
} else {
    # SDL3 needs the JIS DBE key direction correction before events reach SDL2.
    Push-Location $PSScriptRoot
    try {
        cmd /c scripts\build-sdl3-jis.bat
        if ($LASTEXITCODE -ne 0) { throw 'Patched SDL3 build failed' }
    } finally {
        Pop-Location
    }
}

Write-Host "Dependencies successfully deployed" -ForegroundColor Green
