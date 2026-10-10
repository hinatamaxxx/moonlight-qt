param([string]$SourceDirectory)

$ErrorActionPreference = 'Stop'
function Get-TaskSha256([string]$Path) {
    $TaskHasher = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($TaskHasher.ComputeHash([IO.File]::ReadAllBytes($Path)))).Replace('-', '').ToLowerInvariant()
    } finally { $TaskHasher.Dispose() }
}
$TaskRepoRoot = Split-Path $PSScriptRoot -Parent
$TaskSourceCommit = '829a65d769d935c4852f8159e964312c0957260a'
$TaskPatch = Join-Path $PSScriptRoot 'patches\sdl3-jis-toggle.patch'
$TaskBuildRoot = Join-Path $env:LOCALAPPDATA 'Moonlight-SDL3-JIS'
$TaskRuntimeDirectory = Join-Path $TaskRepoRoot 'libs\windows\lib\x64'
$TaskTools = Join-Path $TaskBuildRoot 'tools-4'
$TaskCMake = Join-Path $TaskTools 'cmake\data\bin\cmake.exe'
if (-not (Test-Path -LiteralPath $TaskCMake)) {
    python -m pip install --target $TaskTools cmake==4.4.4
    if ($LASTEXITCODE -ne 0) { throw 'CMake installation failed' }
}
if (-not $SourceDirectory) {
    $SourceDirectory = Join-Path $TaskBuildRoot 'source'
    if (-not (Test-Path (Join-Path $SourceDirectory '.git'))) {
        New-Item -ItemType Directory -Path $TaskBuildRoot -Force | Out-Null
        git clone --depth 1 --branch release-3.4.18 https://github.com/libsdl-org/SDL.git $SourceDirectory
        if ($LASTEXITCODE -ne 0) { throw 'SDL3 source download failed' }
    }
}
$SourceDirectory = [IO.Path]::GetFullPath($SourceDirectory)
if ((git -C $SourceDirectory rev-parse HEAD).Trim() -ne $TaskSourceCommit) { throw 'Unexpected SDL3 source revision' }
$TaskSourceDiff = (git -C $SourceDirectory diff --no-ext-diff) -join "`n"
$TaskExpectedDiff = (Get-Content -LiteralPath $TaskPatch) -join "`n"
if (-not $TaskSourceDiff) {
    git -C $SourceDirectory apply --check $TaskPatch
    if ($LASTEXITCODE -ne 0) { throw 'SDL3 patch does not apply' }
    git -C $SourceDirectory apply $TaskPatch
    if ($LASTEXITCODE -ne 0) { throw 'SDL3 patch application failed' }
}
$TaskSourceDiff = (git -C $SourceDirectory diff --no-ext-diff) -join "`n"
if ($TaskSourceDiff -ne $TaskExpectedDiff) { throw 'Unexpected SDL3 source modifications' }

$TaskBuildDirectory = Join-Path $TaskBuildRoot 'build-x64-cmake4'
& $TaskCMake -S $SourceDirectory -B $TaskBuildDirectory -G $env:TASK_CMAKE_GENERATOR -A x64 -DSDL_SHARED=ON -DSDL_STATIC=OFF -DSDL_TESTS=OFF -DSDL_TEST_LIBRARY=OFF -DSDL_EXAMPLES=OFF -DSDL_INSTALL=OFF
if ($LASTEXITCODE -ne 0) { throw "SDL3 CMake configuration failed (exit $LASTEXITCODE)" }
& $TaskCMake --build $TaskBuildDirectory --config Release --parallel 6
if ($LASTEXITCODE -ne 0) { throw 'SDL3 build failed' }
$TaskDll = Join-Path $TaskBuildDirectory 'Release\SDL3.dll'
Copy-Item -LiteralPath $TaskDll -Destination (Join-Path $TaskRuntimeDirectory 'SDL3.dll') -Force
Copy-Item -LiteralPath (Join-Path $SourceDirectory 'LICENSE.txt') -Destination (Join-Path $TaskRuntimeDirectory 'SDL3-LICENSE.txt') -Force
# The upstream PDB belongs to a different binary.
$TaskOldPdb = Join-Path $TaskRuntimeDirectory 'SDL3.pdb'
if (Test-Path -LiteralPath $TaskOldPdb) { Remove-Item -LiteralPath $TaskOldPdb }
$TaskMetadata = [ordered]@{
    version = '3.4.18'
    sourceCommit = $TaskSourceCommit
    patchSha256 = Get-TaskSha256 $TaskPatch
    dllSha256 = Get-TaskSha256 $TaskDll
    correction = 'Windows JIS DBE toggle decoding and keyboard-grab modifier forwarding'
}
$TaskMetadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $TaskRuntimeDirectory 'SDL3-jis-build.json') -Encoding UTF8
Write-Host 'Patched SDL3 3.4.18 runtime deployed.'
