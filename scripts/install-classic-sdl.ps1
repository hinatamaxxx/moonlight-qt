param(
    [Parameter(Mandatory = $true)][string]$RuntimeDirectory,
    [string]$SourceArchive
)

$ErrorActionPreference = 'Stop'
$TaskPin = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'classic-sdl.json') -Raw | ConvertFrom-Json
$TaskRuntime = (Resolve-Path -LiteralPath $RuntimeDirectory).Path

if (-not $SourceArchive) {
    $TaskCache = Join-Path (Split-Path $PSScriptRoot -Parent) 'libs\classic-sdl-cache'
    New-Item -ItemType Directory -Path $TaskCache -Force | Out-Null
    $SourceArchive = Join-Path $TaskCache 'v6.1.0-jp-keyboard-fix.1.zip'
    if (-not (Test-Path -LiteralPath $SourceArchive)) {
        curl.exe -s -L -f -o $SourceArchive $TaskPin.archiveUrl
        if ($LASTEXITCODE -ne 0) { throw 'Classic SDL source archive download failed' }
    }
}

if ((Get-FileHash -LiteralPath $SourceArchive -Algorithm SHA256).Hash -ne $TaskPin.archiveSha256) {
    throw 'Classic SDL source archive SHA256 mismatch'
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$TaskZip = [IO.Compression.ZipFile]::OpenRead((Resolve-Path -LiteralPath $SourceArchive).Path)
try {
    $TaskEntry = $TaskZip.GetEntry('SDL2.dll')
    if (-not $TaskEntry -or $TaskEntry.Length -gt 10000000) { throw 'Invalid classic SDL archive entry' }
    $TaskInput = $TaskEntry.Open()
    $TaskMemory = New-Object IO.MemoryStream
    try {
        $TaskInput.CopyTo($TaskMemory)
        $TaskBytes = $TaskMemory.ToArray()
    } finally {
        $TaskInput.Dispose()
        $TaskMemory.Dispose()
    }
} finally {
    $TaskZip.Dispose()
}

$TaskHasher = [Security.Cryptography.SHA256]::Create()
try {
    $TaskDigest = [BitConverter]::ToString($TaskHasher.ComputeHash($TaskBytes)).Replace('-', '').ToLowerInvariant()
} finally { $TaskHasher.Dispose() }
if ($TaskDigest -ne $TaskPin.dllSha256) { throw 'Classic SDL DLL SHA256 mismatch' }

# Keep upstream headers/import libraries and other v19 dependencies. SDL2 has
# a stable DLL ABI; the package test verifies actual loading and startup.
[IO.File]::WriteAllBytes((Join-Path $TaskRuntime 'SDL2.dll'), $TaskBytes)
# The v19 PDB describes sdl2-compat, not this classic SDL binary.
$TaskIncompatiblePdb = Join-Path $TaskRuntime 'SDL2.pdb'
if (Test-Path -LiteralPath $TaskIncompatiblePdb) {
    Remove-Item -LiteralPath $TaskIncompatiblePdb -Force
}
Write-Host "Installed pinned classic SDL $($TaskPin.version) x64 runtime ($TaskDigest)"
